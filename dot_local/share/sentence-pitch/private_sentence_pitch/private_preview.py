#!/usr/bin/env python3
"""
Preview without writing anything: color a sample of sentences and save them as an
HTML page styled like your cards, plus an accuracy report.

  python3 preview.py            # 50 random subs2srs sentences
  python3 preview.py 200 7      # 200 sentences, random seed 7

Needs Anki (AnkiConnect) and Brave (Yomitan API) open.
"""
import json
import os
import random
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
USER = os.path.join(HERE, "user_files")


def anki(action, **params):
    req = urllib.request.Request("http://127.0.0.1:8765", data=json.dumps(
        {"action": action, "version": 6, "params": params}).encode())
    with urllib.request.urlopen(req, timeout=120) as r:
        res = json.loads(r.read().decode())
    if res.get("error"):
        raise RuntimeError(f"AnkiConnect {action}: {res['error']}")
    return res["result"]


def notes(note_type):
    ids = anki("findNotes", query=f'"note:{note_type}"')
    for i in range(0, len(ids), 500):
        for n in anki("notesInfo", notes=ids[i:i + 500]):
            yield {k: v["value"] for k, v in n["fields"].items()}


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    cfg = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))
    os.makedirs(USER, exist_ok=True)
    paths = {k: os.path.join(USER, f) for k, f in (("y", "yomitan_cache.json"), ("o", "ojad_cache.json"))}
    yomitan_cache, ojad_cache = core.load_cache(paths["y"]), core.load_cache(paths["o"])

    lookup = core.Lookup(cfg["yomitan_url"], yomitan_cache)
    for v in cfg["vocab"]:
        for f in notes(v["note_type"]):
            if v["word_field"] in f:
                lookup.add_card(f[v["word_field"]], f.get(v["reading_field"], ""),
                                f.get(v["category_field"], ""), v["note_type"])
    lookup.ping()

    spec = cfg["sentences"][0]
    pool = [f for f in notes(spec["note_type"]) if core.clean(f.get(spec["sentence_field"], ""))]
    random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    sample = random.sample(pool, min(n, len(pool)))
    jobs = [{"raw": f[spec["sentence_field"]], "written": f.get(spec.get("written_field") or "", ""),
             "word": f.get(spec["word_field"], ""), "cat": f.get(spec["category_field"], ""),
             "furigana": spec.get("furigana", False)} for f in sample]

    analyzer = core.Analyzer(os.path.expanduser(cfg["python"]), os.path.join(HERE, "analyze.py"))
    lookup.lone = (lambda w, pos: core.lone_category(analyzer, w, pos)) if cfg.get("tiebreak", True) else False
    try:
        results = []
        for i in range(0, len(jobs), 25):
            results += core.process_batch(jobs[i:i + 25], analyzer, lookup, cfg.get("contour", "ojad"),
                                          cfg.get("ojad_interval_seconds", 10), ojad_cache)
    finally:
        analyzer.close()
        core.save_cache(paths["y"], yomitan_cache)
        core.save_cache(paths["o"], ojad_cache)

    total, blocks = {}, []
    for job, (html, stats, _) in zip(jobs, results):
        core.merge_stats(total, stats)
        miss = "<br>".join(core.esc(u) for u in dict.fromkeys(stats.get("uncolored", [])))
        blocks.append(f'<section><div class="meta">{core.esc(core.clean(job["word"]))} · '
                      f'{core.esc(core.first_cat(job["cat"]) or "-")}</div>'
                      f'<div id="sentence">{html}</div><div class="miss">{miss}</div></section>')

    css = anki("modelStyling", modelName=spec["note_type"])["css"]
    css += open(os.path.join(HERE, "card.css"), encoding="utf-8").read()
    css += """
body { max-width: 900px; margin: 0 auto; padding: 16px; }
section { border-bottom: 1px solid #555; padding: 0.5rem 0 1rem; }
.meta, .miss { font-family: -apple-system, sans-serif; opacity: 0.55; }
.meta { font-size: 0.8rem; } .miss { font-size: 0.7rem; }"""
    media = urllib.request.pathname2url(anki("getMediaDirPath")) + "/"
    page = (f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            f'<base href="file://{media}"><title>Sentence pitch preview</title>'
            f'<style>{css}</style><body class="card">' + "".join(blocks) + "</body>")
    with open(os.path.join(USER, "preview.html"), "w", encoding="utf-8") as f:
        f.write(page)

    report = core.format_report(len(jobs), total, conflicts=lookup.conflicts())
    with open(os.path.join(USER, "preview_report.txt"), "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print(f"\nYomitan lookups: {lookup.lookups}")
    print(f"Preview: {os.path.join(USER, 'preview.html')}")


if __name__ == "__main__":
    main()
