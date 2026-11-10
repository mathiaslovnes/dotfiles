#!/usr/bin/env python3
"""PreToolUse hook for Claude Code's Bash tool: refuse file edits made from the shell.

Claude must change files with its Edit/Write tools so the user sees a diff
(~/.claude/CLAUDE.md, "File edits"). This hook blocks the two shell ways around that:

  1. In-place edits: sed -i / --in-place and perl -i, also when run through find -exec or xargs.
  2. Heredocs written to a file: cat > f <<EOF, cat <<EOF >> f, tee f <<EOF, ... <<EOF | tee f.

Allowed: anything that only writes under /tmp or /private/tmp (Claude's scratchpad lives there),
and commands that don't write files: sed -n, piped sed, python3 - <<EOF, git commit heredocs.

Claude Code passes the tool call as JSON on stdin. Exit 0 allows the command; exit 2 blocks it
and shows the stderr message to Claude, which then uses Edit/Write instead.
"""

import json
import re
import shlex
import sys

# --- Settings ----------------------------------------------------------------------------------

SCRATCH_PREFIXES = ("/tmp/", "/private/tmp/")
HARMLESS_TARGETS = {"/dev/null", "/dev/stdout", "/dev/stderr"}
EDITORS = {"sed", "gsed", "perl"}

BLOCK_MESSAGE = (
    "Blocked: change files with the Edit or Write tool, not sed -i, perl -i or heredocs "
    "(see ~/.claude/CLAUDE.md). Files under /tmp or /private/tmp are fine."
)

PIPELINE_SEPARATORS = {";", ";;", "&&", "||", "&", "(", ")"}
PIPE_SEPARATORS = {"|", "|&"}
REDIRECTS = {">", ">>", ">|", "&>", "&>>"}

# --- Parsing the command -----------------------------------------------------------------------

# <<EOF, <<-EOF, <<'EOF', <<"EOF", but not the here-string <<<
HEREDOC_START = re.compile(r"(?<!<)<<(?!<)-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def strip_heredoc_bodies(cmd):
    """Drop heredoc bodies, so text inside them isn't parsed as commands."""
    kept, pending = [], []
    for line in cmd.split("\n"):
        if pending:
            if line.strip() == pending[0]:
                pending.pop(0)
            continue
        kept.append(line)
        pending.extend(m.group(2) for m in HEREDOC_START.finditer(line))
    return "\n".join(kept)


def tokenize(cmd):
    """Split into shell words, with ; | && > << and friends as separate tokens."""
    cmd = cmd.replace("\\\n", " ").replace("\n", " ; ")
    lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    return list(lexer)


def pipelines(tokens):
    """Group tokens into pipelines (split on ; && || &), each a list of commands (split on |)."""
    pipeline, command = [], []
    for tok in tokens:
        if tok in PIPELINE_SEPARATORS:
            pipeline.append(command)
            yield pipeline
            pipeline, command = [], []
        elif tok in PIPE_SEPARATORS:
            pipeline.append(command)
            command = []
        else:
            command.append(tok)
    pipeline.append(command)
    yield pipeline


def is_scratch(path):
    return path in HARMLESS_TARGETS or path.startswith(SCRATCH_PREFIXES)


# --- Check 1: in-place edits with sed or perl --------------------------------------------------


def sed_edit(args):
    """Return (in_place, files) for sed's arguments."""
    in_place, script_given, positional = False, False, []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-e", "--expression", "-f", "--file"):
            script_given = True
            i += 1  # skip the script or script file
        elif arg.startswith(("--expression=", "--file=")):
            script_given = True
        elif arg == "--in-place" or arg.startswith("--in-place="):
            in_place = True
        elif arg == "-i":
            in_place = True
            if i + 1 < len(args) and (args[i + 1] == "" or args[i + 1].startswith(".")):
                i += 1  # BSD sed's backup suffix: sed -i '' or sed -i .bak
        elif arg.startswith("-") and len(arg) > 1 and not arg.startswith("--"):
            flags = arg[1:]
            if "i" in flags:
                in_place = True  # -Ei, -i.bak
            if flags.endswith(("e", "f")):
                script_given = True
                i += 1  # -ne 'script'
        elif not arg.startswith("--"):
            positional.append(arg)
        i += 1
    files = positional if script_given else positional[1:]
    return in_place, files


def perl_edit(args):
    """Return (in_place, files) for perl's arguments."""
    in_place, script_given, positional = False, False, []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("-") and len(arg) > 1 and not positional:
            for pos, flag in enumerate(arg[1:]):
                if flag in "MmIxCd0l":
                    break  # the rest of the token is this flag's argument (-Mstrict, -0777)
                if flag == "i":
                    in_place = True
                    break  # the rest is a backup suffix (-i.bak)
                if flag in "eE":
                    script_given = True
                    if pos == len(arg) - 2:
                        i += 1  # code is the next token (-pe 'code')
                    break
        else:
            positional.append(arg)
        i += 1
    files = positional if script_given else positional[1:]
    return in_place, files


def in_place_edit(command):
    """If the command runs sed/perl in place on a non-scratch file, describe it."""
    for idx, tok in enumerate(command):
        prog = tok.rsplit("/", 1)[-1]
        if prog not in EDITORS:
            continue
        args = command[idx + 1:]
        in_place, files = (perl_edit if prog == "perl" else sed_edit)(args)
        if not in_place:
            return None
        outside = [f for f in files if not is_scratch(f)]
        if not files:
            return f"{prog} -i on files from find/xargs"
        if outside:
            return f"{prog} -i on {outside[0]}"
    return None


# --- Check 2: heredocs written to a file -------------------------------------------------------


def write_targets(command):
    """Files a command writes: redirect targets, plus tee's file arguments."""
    targets = [command[j + 1] for j, tok in enumerate(command[:-1]) if tok in REDIRECTS]
    if command and command[0].rsplit("/", 1)[-1] == "tee":
        args = iter(command[1:])
        for arg in args:
            if arg and arg[0] in "<>&":
                next(args, None)  # an operator and its operand (<<EOF, >file), not a tee file
            elif not arg.startswith("-"):
                targets.append(arg)
    return targets


def heredoc_write(pipeline):
    """If a pipeline feeds a heredoc into a non-scratch file, describe it."""
    if not any(tok in ("<<", "<<-", "<<<") for command in pipeline for tok in command):
        return None
    for command in pipeline:
        outside = [t for t in write_targets(command) if not is_scratch(t)]
        if outside:
            return f"heredoc written to {outside[0]}"
    return None


# --- Main --------------------------------------------------------------------------------------


def find_shell_edit(cmd):
    try:
        tokens = tokenize(strip_heredoc_bodies(cmd))
    except ValueError:
        return None  # unbalanced quotes: bash would reject the command anyway
    for pipeline in pipelines(tokens):
        reason = heredoc_write(pipeline)
        for command in pipeline:
            reason = reason or in_place_edit(command)
        if reason:
            return reason
    return None


def main():
    try:
        cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    except (json.JSONDecodeError, AttributeError):
        return 0
    reason = find_shell_edit(cmd)
    if reason:
        print(f"{BLOCK_MESSAGE} ({reason})", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
