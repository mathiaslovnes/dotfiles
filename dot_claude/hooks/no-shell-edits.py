#!/usr/bin/env python3
"""PreToolUse hook for Claude Code's Bash tool: refuse file edits made from the shell.

Claude must change files with its Edit/Write tools so the user sees a diff
(~/.claude/CLAUDE.md, "File edits"). This hook blocks the two shell ways around that:

  1. In-place edits: sed -i / --in-place and perl -i, also when run through find -exec or xargs.
  2. Heredocs written to a file by cat or tee: cat > f <<EOF, tee f <<EOF, cat <<EOF | tee f.

Allowed: anything that only writes under /tmp or /private/tmp (Claude's scratchpad lives there),
and commands that don't write a heredoc's text to a file: sed -n, piped sed, python3 - <<EOF
(also with its output redirected), git commit heredocs.

Claude Code passes the tool call as JSON on stdin. Exit 0 allows the command; exit 2 blocks it
and shows the stderr message to Claude, which then uses Edit/Write instead.
"""

import json
import os
import re
import shlex
import sys

# --- Settings ----------------------------------------------------------------------------------

SCRATCH_PREFIXES = ("/tmp/", "/private/tmp/")
HARMLESS_TARGETS = {"/dev/null", "/dev/stdout", "/dev/stderr"}
EDITORS = {"sed", "gsed", "perl"}
HEREDOC_WRITERS = {"cat", "tee"}

BLOCK_MESSAGE = (
    "Blocked: change files with the Edit or Write tool, not sed -i, perl -i or heredocs "
    "(see ~/.claude/CLAUDE.md). Files under /tmp or /private/tmp are fine."
)

PIPELINE_SEPARATORS = {";", ";;", "&&", "||", "&", "(", ")"}
PIPE_SEPARATORS = {"|", "|&"}
REDIRECTS = {">", ">>", ">|", "&>", "&>>"}
HEREDOC_OPERATORS = {"<<", "<<-", "<<<"}

HOME = os.path.expanduser("~")

# --- Parsing the command -----------------------------------------------------------------------

# <<EOF, <<-EOF, <<'EOF', <<"EOF", matched at a position already known not to be <<<
HEREDOC_START = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def heredoc_delimiters(line, state):
    """Delimiters of heredocs started on this line.

    Skips << inside quotes and $((...)) arithmetic. `state` carries the open quote and
    arithmetic depth over to the next line, for strings that span lines.
    """
    delimiters, i = [], 0
    while i < len(line):
        if state["quote"]:
            if line[i] == "\\" and state["quote"] == '"':
                i += 2
                continue
            if line[i] == state["quote"]:
                state["quote"] = None
        elif line[i] == "\\":
            i += 2
            continue
        elif line[i] in "'\"":
            state["quote"] = line[i]
        elif line.startswith("$((", i):
            state["arith"] += 1
            i += 3
            continue
        elif state["arith"] and line.startswith("))", i):
            state["arith"] -= 1
            i += 2
            continue
        elif not state["arith"] and line.startswith("<<<", i):
            i += 3  # here-string, has no body
            continue
        elif not state["arith"] and line.startswith("<<", i):
            match = HEREDOC_START.match(line, i)
            if match:
                delimiters.append(match.group(2))
                i = match.end()
                continue
        i += 1
    return delimiters


def strip_heredoc_bodies(cmd):
    """Drop heredoc bodies, so text inside them isn't parsed as commands."""
    kept, pending, state = [], [], {"quote": None, "arith": 0}
    for line in cmd.split("\n"):
        if pending:
            if line.strip() == pending[0]:
                pending.pop(0)
            continue
        kept.append(line)
        pending.extend(heredoc_delimiters(line, state))
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


def program(command):
    return command[0].rsplit("/", 1)[-1] if command else ""


# --- Paths -------------------------------------------------------------------------------------


def resolve(path, cwd):
    """Absolute path for a target, relative to the directory the command runs in."""
    if path in HARMLESS_TARGETS:
        return path
    if path.startswith("~"):
        path = os.path.expanduser(path)
    elif path.startswith(("$HOME", "${HOME}")):
        path = HOME + path.split("}", 1)[-1] if path.startswith("${") else HOME + path[5:]
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    return os.path.normpath(path)


def is_scratch(path, cwd):
    resolved = resolve(path, cwd)
    return resolved in HARMLESS_TARGETS or (resolved + "/").startswith(SCRATCH_PREFIXES)


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


def perl_flags(flags):
    """Read one perl switch cluster (-0pi, -lne, -Mstrict). Return (in_place, code_follows, code_given)."""
    in_place = code_given = code_follows = False
    j = 0
    while j < len(flags):
        flag = flags[j]
        j += 1
        if flag == "0":  # -0, -0777, -0xHH: the digits belong to -0
            if j < len(flags) and flags[j] in "xX":
                j += 1
                while j < len(flags) and flags[j] in "0123456789abcdefABCDEF":
                    j += 1
            while j < len(flags) and flags[j].isdigit():
                j += 1
        elif flag == "l":  # -l, -l012
            while j < len(flags) and flags[j].isdigit():
                j += 1
        elif flag in "MmIxCd":
            break  # the rest of the cluster is this switch's argument
        elif flag == "i":
            in_place = True
            break  # the rest is a backup suffix (-i.bak)
        elif flag in "eE":
            code_given = True
            code_follows = j == len(flags)  # -pe 'code' vs -e'code'
            break
    return in_place, code_follows, code_given


def perl_edit(args):
    """Return (in_place, files) for perl's arguments."""
    in_place, script_given, positional = False, False, []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("-") and len(arg) > 1 and not positional:
            cluster_in_place, code_follows, code_given = perl_flags(arg[1:])
            in_place = in_place or cluster_in_place
            script_given = script_given or code_given
            if code_follows:
                i += 1  # skip the code
        else:
            positional.append(arg)
        i += 1
    files = positional if script_given else positional[1:]
    return in_place, files


def find_start_dirs(command):
    """The directories a find command searches: its arguments before the first option."""
    starts = []
    for tok in command[1:]:
        if tok.startswith("-") or tok in ("!", "\\("):
            break
        starts.append(tok)
    return starts or ["."]


def in_place_edit(command, cwd):
    """If the command runs sed/perl in place on a non-scratch file, describe it."""
    for idx, tok in enumerate(command):
        prog = tok.rsplit("/", 1)[-1]
        if prog not in EDITORS:
            continue
        in_place, files = (perl_edit if prog == "perl" else sed_edit)(command[idx + 1:])
        if not in_place:
            return None
        if program(command) == "find":  # find ... -exec sed -i ... {} +
            starts = find_start_dirs(command)
            files = [s for f in files if f not in ("+", ";") for s in (starts if f == "{}" else [f])]
        if not files:
            return f"{prog} -i on files from xargs"
        outside = [f for f in files if not is_scratch(f, cwd)]
        if outside:
            return f"{prog} -i on {outside[0]}"
        return None
    return None


# --- Check 2: heredocs written to a file -------------------------------------------------------


def write_targets(command):
    """Files a command writes: redirect targets, plus tee's file arguments."""
    targets = [command[j + 1] for j, tok in enumerate(command[:-1]) if tok in REDIRECTS]
    if program(command) == "tee":
        args = iter(command[1:])
        for arg in args:
            if arg and arg[0] in "<>&":
                next(args, None)  # an operator and its operand (<<EOF, >file), not a tee file
            elif not arg.startswith("-"):
                targets.append(arg)
    return targets


def heredoc_write(pipeline, cwd):
    """If a heredoc's own text goes into a non-scratch file, describe it.

    That happens when cat or tee receives the heredoc and writes it out (cat > f <<EOF,
    tee f <<EOF), or when cat <<EOF is piped into tee. A heredoc that feeds another program
    (python3 - <<EOF > out.json) only writes that program's output, which is allowed.
    """
    for k, command in enumerate(pipeline):
        if program(command) not in HEREDOC_WRITERS or not HEREDOC_OPERATORS & set(command):
            continue
        targets = write_targets(command)
        if program(command) == "cat":
            targets += [t for later in pipeline[k + 1:] if program(later) == "tee"
                        for t in write_targets(later)]
        outside = [t for t in targets if not is_scratch(t, cwd)]
        if outside:
            return f"heredoc written to {outside[0]}"
    return None


# --- Main --------------------------------------------------------------------------------------


def find_shell_edit(cmd, cwd):
    try:
        tokens = tokenize(strip_heredoc_bodies(cmd))
    except ValueError:
        return None  # unbalanced quotes: bash would reject the command anyway
    for pipeline in pipelines(tokens):
        if len(pipeline) == 1 and program(pipeline[0]) == "cd":  # cd dir && ... changes cwd
            args = pipeline[0][1:]
            if not args or args[0] != "-":
                cwd = resolve(args[0], cwd) if args else HOME
            continue
        reason = heredoc_write(pipeline, cwd)
        for command in pipeline:
            reason = reason or in_place_edit(command, cwd)
        if reason:
            return reason
    return None


def main():
    try:
        call = json.load(sys.stdin)
        cmd = call.get("tool_input", {}).get("command", "")
        cwd = call.get("cwd") or os.getcwd()
    except (json.JSONDecodeError, AttributeError):
        return 0
    reason = find_shell_edit(cmd, cwd)
    if reason:
        print(f"{BLOCK_MESSAGE} ({reason})", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
