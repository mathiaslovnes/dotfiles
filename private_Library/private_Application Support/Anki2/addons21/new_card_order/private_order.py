"""
The ordering itself, without Anki: which new card comes when.

Each new card teaches one word (its card's word). A card's other words are
  known      in a card you've already reviewed (its own vocab card, or any studied sentence)
  taught     unknown, but a new card from another sentence teaches it: that card comes first
  unknown    everything else you haven't met: words no new card teaches, and the words of
             the other new cards made from the same sentence

score s(c): the average frequency rank of the card's word and its unknown words, but never
  better than the card's word alone (a common word you happen not to have met shouldn't move a
  sentence forward). With rule "most_common": the smallest of those ranks.
urgency e(c) = min(s(c), e(d) for every card d waiting on c): a prerequisite moves forward
  when a better card depends on it.
Order: repeatedly the ready card with the lowest urgency. A card comes at least one day's worth
  of new cards after the card teaching a word it needs, and after any other card made from the
  same sentence, unless nothing else is left to fill the place (the report lists those).
"""
import heapq
import statistics


def build(cards, deps, known, rank, rule="average", one_day=25):
    """cards: [{"cid", "nid", "key", "rank", "due", "group"}] the new cards to order; group:
    cards made from the same sentence share it.  deps: {nid: [word key, ...]} the words of each
    card's sentence.  known: {word key}.  rank: word key -> frequency rank (smaller = more common)
    -> (card ids in order, {cid: details}, summary)"""
    by_id = {c["cid"]: c for c in cards}
    teachers, groups = {}, {}
    for c in cards:
        teachers.setdefault(c["key"], []).append(c["cid"])
        groups.setdefault(c["group"], []).append(c["cid"])
    info = {}
    for c in cards:
        others = set(deps.get(c["nid"], ())) - {c["key"]}
        group_words = {by_id[d]["key"] for d in groups[c["group"]] if d != c["cid"]}
        others |= group_words
        unknown = {w for w in others if w not in known}
        prereq = {w for w in unknown
                  if any(by_id[t]["group"] != c["group"] for t in teachers.get(w, ()))}
        rest = unknown - prereq
        ranks = [c["rank"]] + [rank(w) for w in sorted(rest)]
        s = min(ranks) if rule == "most_common" else max(c["rank"], statistics.fmean(ranks))
        info[c["cid"]] = {"s": s, "e": s, "prereq": prereq, "unknown": {w: rank(w) for w in rest}}

    waiting_on = {}  # teacher -> cards waiting for its word
    for cid, d in info.items():
        for w in d["prereq"]:
            for t in teachers[w]:
                if by_id[t]["group"] != by_id[cid]["group"]:
                    waiting_on.setdefault(t, []).append(cid)
    changed = True
    while changed:
        changed = False
        for t, ds in waiting_on.items():
            best = min(info[d]["e"] for d in ds)
            if best < info[t]["e"]:
                info[t]["e"] = best
                changed = True

    def priority(cid):
        return (info[cid]["e"], info[cid]["s"], by_id[cid]["due"], cid)

    missing = {cid: set(d["prereq"]) for cid, d in info.items()}
    needs = {}
    for cid, ws in missing.items():
        for w in ws:
            needs.setdefault(w, []).append(cid)
    taught_at, group_at = {}, {}  # word -> first position teaching it; group -> last position used
    ready, cooling = [], []  # (priority, cid) / (from position, priority, cid)
    for cid, ws in missing.items():
        if not ws:
            heapq.heappush(ready, (priority(cid), cid))
    placed, order = set(), []
    summary = {"short": [], "cycles": 0, "waiting": sum(1 for d in info.values() if d["prereq"]),
               "shared": sum(1 for g in groups.values() if len(g) > 1)}

    def free_from(cid):
        """First position where the card keeps a day from what it needs and from its sentence."""
        at = [taught_at[w] + one_day for w in info[cid]["prereq"] if w in taught_at]
        g = by_id[cid]["group"]
        if g in group_at:
            at.append(group_at[g] + one_day)
        return max(at, default=0)

    while len(order) < len(cards):
        pos = len(order)
        while cooling and cooling[0][0] <= pos:
            _, p, cid = heapq.heappop(cooling)
            heapq.heappush(ready, (p, cid))
        cid = None
        while ready:
            p, c = heapq.heappop(ready)
            if c in placed:
                continue
            f = free_from(c)
            if f > pos:  # a card from its sentence came less than a day ago
                heapq.heappush(cooling, (f, p, c))
                continue
            cid = c
            break
        if cid is None and cooling:  # nothing else left: less than a day after what it needs
            i = min(range(len(cooling)), key=lambda k: cooling[k][1])
            cid = cooling.pop(i)[2]
            heapq.heapify(cooling)
            summary["short"].append(cid)
        if cid is None:  # cards waiting on each other's words: the most urgent first
            cid = min((c for c in missing if c not in placed), key=priority)
            summary["cycles"] += 1
        placed.add(cid)
        order.append(cid)
        info[cid]["pos"] = pos
        group_at[by_id[cid]["group"]] = pos
        w = by_id[cid]["key"]
        if w in taught_at:
            continue
        taught_at[w] = pos
        for d in needs.get(w, ()):
            if d in placed or w not in missing[d] or by_id[d]["group"] == by_id[cid]["group"]:
                continue
            missing[d].discard(w)
            if not missing[d]:
                heapq.heappush(cooling, (free_from(d), priority(d), d))
    for cid, d in info.items():
        d["after"] = {w: taught_at.get(w) for w in d["prereq"]}
        sibs = [info[s]["pos"] for s in groups[by_id[cid]["group"]] if s != cid and info[s]["pos"] < d["pos"]]
        d["sibling"] = max(sibs) if sibs else None
        d["gap_ok"] = (all(t is not None and d["pos"] - t >= one_day for t in d["after"].values())
                       and (d["sibling"] is None or d["pos"] - d["sibling"] >= one_day))
    return order, info, summary
