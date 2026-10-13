#!/usr/bin/env python3
"""
Sentence analysis with pyopenjtalk. Runs in its own Python (the venv), never inside Anki.

Protocol: one JSON list of strings per line on stdin; for each, one JSON line on
stdout with one entry per string: a list of word nodes, or {"error": "..."}.
"""
import contextlib
import json
import sys

import pyopenjtalk

KEYS = ("string", "pos", "pos_group1", "ctype", "cform", "orig", "read", "pron",
        "acc", "mora_size", "chain_flag")


def analyze(text):
    if not text.strip():
        return []
    return [{k: n[k] for k in KEYS} for n in pyopenjtalk.run_frontend(text)]


def main():
    with contextlib.redirect_stdout(sys.stderr):  # first run downloads the dictionary and prints
        pyopenjtalk.g2p("あ")
    for line in sys.stdin:
        out = []
        for text in json.loads(line):
            try:
                out.append(analyze(text))
            except Exception as e:
                out.append({"error": f"{type(e).__name__}: {e}"})
        sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
