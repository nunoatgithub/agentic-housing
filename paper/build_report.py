"""Builds REPORT.md from paper/REPORT.template.md and the saved runs in runs/.

    python paper/build_report.py

Every number in the report is computed here from the saved records, following paper/ANALYSIS_PLAN.md.
"""
import itertools
import math
import re
import statistics as st
import sys
import textwrap
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from house.experiment import PATCHES, STEPS, Label, final_house, load_runs, parse_label, scores_of  # noqa: E402
from house.layout_format import parse_layout  # noqa: E402
from house.model import COLS, ROWS  # noqa: E402
from house.render import Drawing, render_side_by_side  # noqa: E402
from house.rules import door_graph, entrance_rooms  # noqa: E402
from house.scores import DESTINATIONS, _depths  # noqa: E402

EFFORT = "medium"
CELLS = ROWS * COLS
SCORES = ("corridor_rooms", "privacy_order", "walking_distance", "compactness")
NAMES = ("Corridor rooms", "Privacy order", "Walking distance", "Compactness")
ARMS = (("A", "A (first house)"), ("H", "H (patched step by step)"), ("I", "I (planned from scratch)"), ("J", "J (patched in one go)"))


def md(rows):
    head, *body = rows
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"] + ["| " + " | ".join(r) + " |" for r in body])


def ms(v):
    return ("%.2f ± %.2f" % (st.mean(v), st.stdev(v))) if len(v) > 1 else ("%.2f" % v[0] if v else "–")


def perm_p(a, b):
    """Two-sided exact permutation test on the difference of means."""
    pool, n = a + b, len(a)
    observed = abs(st.mean(a) - st.mean(b))
    hits = total = 0
    for idx in itertools.combinations(range(len(pool)), n):
        group = [pool[i] for i in idx]
        rest = [pool[i] for i in range(len(pool)) if i not in idx]
        total += 1
        hits += abs(st.mean(group) - st.mean(rest)) >= observed - 1e-12
    return hits / total


def ranks(x):
    order = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def ranksum_p(a, b):
    """Exact two-sided rank-sum (Mann-Whitney) permutation test, ties handled with mid-ranks."""
    pool, n = a + b, len(a)
    rk = ranks(pool)
    obs = sum(rk[:n])
    mean = n * (len(pool) + 1) / 2
    hits = total = 0
    for idx in itertools.combinations(range(len(pool)), n):
        total += 1
        hits += abs(sum(rk[i] for i in idx) - mean) >= abs(obs - mean) - 1e-9
    return hits / total


def fisher(a, b, c, d):
    """Two-sided exact p for the 2x2 table [[a, b], [c, d]]."""
    n1, n2, k = a + b, c + d, a + c
    pr = lambda x: math.comb(n1, x) * math.comb(n2, k - x) / math.comb(n1 + n2, k)
    obs = pr(a)
    return sum(pr(x) for x in range(max(0, k - n2), min(n1, k) + 1) if pr(x) <= obs + 1e-12)


def shape(layout):
    """A house up to the names of its rooms: the room type in each cell and the doors."""
    cells = tuple(sorted((str(c), r.type) for r in layout.rooms.values() for c in r.cells))
    doors = tuple(sorted(tuple(sorted(str(x) if x else "out" for x in e.cells())) for e in layout.doors))
    return cells, doors


runs = load_runs(ROOT / "runs")
label = lambda r: parse_label(r["label"])
mine = [r for r in runs if label(r) and label(r).effort == EFFORT]
ok = lambda r: r["accepted"] and r["valid"]
final = {}
for chain in range(1, 7):
    for step in STEPS:
        f = final_house(runs, Label("sonnet55", EFFORT, chain, step))
        if f:
            final[(chain, step)] = (f, scores_of(f), parse_layout(f["layout"]))
chains_of = lambda step: [c for c in range(1, 7) if (c, step) in final]
values = lambda step, score: [final[(c, step)][1][score] for c in chains_of(step)]
T = {}

# ---- completion and failures
def kind(r):
    if not r["accepted"]:
        e = r["errors"][0]["reason"]
        return "syntax" if "cannot understand" in e else ("window" if "outer wall" in e else "other")
    return "rule %s" % "+".join(str(n) for n in sorted({v["rule"] for v in r["violations"]}))


T["n_calls"] = str(len(mine))
T["n_failed"] = str(sum(1 for r in mine if not ok(r)))
T["complete_chains"] = str(sum(1 for c in range(1, 7) if all((c, s) in final for s in STEPS)))
rows = [("Agent", "Calls", "Failed", "Script rejected: line outside the language", "Script rejected: window on a wall that is not outer",
         "Script rejected: other", "House invalid: rule 1", "House invalid: rule 6", "House invalid: other rules")]
for name, steps in (("A (first house)", "A"), ("B–H (patch steps)", "".join(PATCHES)), ("I (planned)", "I"), ("J (patched in one go)", "J")):
    rs = [r for r in mine if label(r).step in steps]
    bad = Counter(kind(r) for r in rs if not ok(r))
    other_invalid = sum(v for k, v in bad.items() if k.startswith("rule") and k not in ("rule 1", "rule 6"))
    rows.append((name, str(len(rs)), str(sum(bad.values())), str(bad["syntax"]), str(bad["window"]), str(bad["other"]),
                 str(bad["rule 1"]), str(bad["rule 6"]), str(other_invalid)))
T["failures"] = md(rows)


def failed(steps):
    rs = [r for r in mine if label(r).step in steps]
    return sum(1 for r in rs if not ok(r)), len(rs)


fi, ni = failed("I")
fp, npatch = failed("".join(PATCHES))
T["planned_fail"], T["patch_fail"] = "%d of %d" % (fi, ni), "%d of %d" % (fp, npatch)
T["p_planned_failures"] = "%.2f" % fisher(fi, ni - fi, fp, npatch - fp)
stopped = []
for c in range(1, 7):
    for step in PATCHES:
        if (c, step) not in final:
            stopped.append("chain %d stopped at step %s" % (c, step))
            break
T["stopped"] = "; ".join(stopped) if stopped else "no patch sequence stopped"
planned_bad = [r for r in mine if label(r).step == "I" and not r["accepted"]]
T["planned_rejected_lines"] = "; ".join(sorted({"`%s`" % r["errors"][0]["text"] for r in planned_bad})) or "none"

# ---- distinct first houses (chains that share one are not independent for H and J)
a_shapes = Counter(shape(final[(c, "A")][2]) for c in chains_of("A"))
T["distinct_A"] = str(len(a_shapes))
T["largest_A_group"] = str(max(a_shapes.values()))
T["distinct_final"] = ", ".join("%s: %d of %d" % (s, len({shape(final[(c, s)][2]) for c in chains_of(s)}), len(chains_of(s))) for s in "HIJ")

# ---- scores of the final houses, with room counts
rows = [("House", "Chains (n)") + NAMES]
for step, name in ARMS:
    rows.append((name, str(len(chains_of(step)))) + tuple(ms(values(step, s)) for s in SCORES))
T["scores"] = md(rows)

rows = [("House", "Score", "Smallest", "Median", "Largest")]
for step, name in ARMS[1:]:
    for s, sname in zip(SCORES, NAMES):
        v = values(step, s)
        rows.append((name, sname, "%.2f" % min(v), "%.2f" % st.median(v), "%.2f" % max(v)))
T["ranges"] = md(rows)

# ---- summary numbers used in the text
finals = [(c, s) for s in "HIJ" for c in chains_of(s)]
T["n_final"] = str(len(finals))
T["corridor_zero_final"] = "%d of %d" % (sum(final[k][1]["corridor_rooms"] == 0 for k in finals), len(finals))
T["privacy_min"] = "%.2f" % min(final[k][1]["privacy_order"] for k in finals)
T["privacy_max"] = "%.2f" % max(final[k][1]["privacy_order"] for k in finals)
for step in "HIJ":
    T["compact_zero_%s" % step] = "%d of %d" % (sum(x == 0 for x in values(step, "compactness")), len(chains_of(step)))
    for s in SCORES:
        T["mean_%s_%s" % (s, step)] = "%.2f" % st.mean(values(step, s))
T["patch_fail_reasons"] = "; ".join(sorted({r["errors"][0]["reason"] if not r["accepted"] else "house broke rule " + ", ".join(str(v["rule"]) for v in r["violations"])
                                            for r in mine if label(r).step in PATCHES and not ok(r)})) or "none"
T["planned_fail_reasons"] = "; ".join(sorted({r["errors"][0]["reason"] if not r["accepted"] else "house broke rule " + ", ".join(sorted({str(v["rule"]) for v in r["violations"]}))
                                              for r in mine if label(r).step == "I" and not ok(r)})) or "none"

# ---- planned tests: permutation tests of means (8)
rows = [("Score", "Patched house", "n (patched vs planned)", "Mean (patched)", "Mean (planned I)", "Exact permutation p")]
pvals = {}
for s, sname in zip(SCORES, NAMES):
    for patched, pname in (("H", "H step by step"), ("J", "J in one go")):
        a, b = values(patched, s), values("I", s)
        constant = len(set(a + b)) == 1
        p = perm_p(a, b)
        pvals[(s, patched)] = p
        rows.append((sname, pname, "%d vs %d" % (len(a), len(b)), "%.2f" % st.mean(a), "%.2f" % st.mean(b),
                     "%.3f%s" % (p, " (all values equal)" if constant else "")))
T["tests"] = md(rows)
T["smallest_p"] = "%.3f" % min(pvals.values())
T["n_informative_tests"] = str(sum(1 for (s, h) in pvals if len(set(values(h, s) + values("I", s))) > 1))
for (s, patched), p in pvals.items():
    T["p_%s_%s" % (s, patched)] = "%.2f" % p

# ---- planned tests: corridor rooms, rank-sum and the count of houses with a score of 3 or more
rows = [("Patched house", "Corridor ≥ 3 (patched)", "Corridor ≥ 3 (planned I)", "Fisher exact p", "Rank-sum exact p")]
for patched, pname in (("H", "H step by step"), ("J", "J in one go")):
    a, b = values(patched, "corridor_rooms"), values("I", "corridor_rooms")
    ka, kb = sum(x >= 3 for x in a), sum(x >= 3 for x in b)
    pf, pr = fisher(ka, len(a) - ka, kb, len(b) - kb), ranksum_p(a, b)
    T["tail_%s" % patched], T["tail_p_%s" % patched], T["ranksum_p_%s" % patched] = "%d of %d" % (ka, len(a)), "%.3f" % pf, "%.3f" % pr
    rows.append((pname, "%d of %d" % (ka, len(a)), "%d of %d" % (kb, len(b)), "%.3f" % pf, "%.3f" % pr))
T["tail_I"] = "%d of %d" % (sum(x >= 3 for x in values("I", "corridor_rooms")), len(values("I", "corridor_rooms")))
T["corridor_tests"] = md(rows)

# ---- along the patch sequence
rows = [("Score",) + tuple("ABCDEFGH")]
for s, sname in zip(SCORES, NAMES):
    rows.append((sname,) + tuple("%.2f" % st.mean(values(step, s)) for step in "ABCDEFGH"))
rows.append(("Chains (n)",) + tuple(str(len(chains_of(step))) for step in "ABCDEFGH"))
T["trajectory"] = md(rows)
free = [CELLS - len(final[(c, "G")][2].rooms) for c in chains_of("G")]
T["free_before_h"] = "%.1f (range %d to %d)" % (st.mean(free), min(free), max(free))

# ---- what the patch agents did: layout unchanged (room type per cell) and rooms removed by the script
cellmap = lambda L: {c: r.type for r in L.rooms.values() for c in r.cells}
same = lambda prev, new: sum(1 for c, t in cellmap(prev).items() if cellmap(new).get(c) == t) / len(cellmap(prev))
per_step, removed, a_to_h = [], [], []
for c in range(1, 7):
    for step in PATCHES:
        prev, cur = final.get((c, chr(ord(step) - 1))), final.get((c, step))
        if prev and cur:
            per_step.append(same(prev[2], cur[2]))
            removed.append(sum(1 for l in cur[0]["script"].splitlines() if l.strip().startswith("remove room")))
    if (c, "A") in final and (c, "H") in final:
        a_to_h.append(same(final[(c, "A")][2], final[(c, "H")][2]))
rows = [("Patch steps", "Removed no room", "Removed 1 room", "Removed 2 or more rooms", "Median share of the previous layout unchanged",
         "Share of the first house (A) unchanged after step H: smallest / median / largest")]
rows.append((str(len(per_step)), str(sum(x == 0 for x in removed)), str(sum(x == 1 for x in removed)), str(sum(x >= 2 for x in removed)),
             "%.2f" % st.median(per_step), "%.2f / %.2f / %.2f" % (min(a_to_h), st.median(a_to_h), max(a_to_h))))
T["patching"] = md(rows)
T["n_patch_steps"] = str(len(per_step))
T["removed_none"] = str(sum(x == 0 for x in removed))

removed_types, replaced = Counter(), Counter()
for c in range(1, 7):
    for step in PATCHES:
        prev, cur = final.get((c, chr(ord(step) - 1))), final.get((c, step))
        if prev and cur:
            for l in cur[0]["script"].splitlines():
                if l.strip().startswith("remove room") and l.split()[2] in prev[2].rooms:
                    r = prev[2].rooms[l.split()[2]]
                    after = cur[2].room_at(next(iter(r.cells)))
                    removed_types[r.type] += 1
                    replaced[after.type if after else "empty"] += 1
T["removed_one"] = str(sum(x == 1 for x in removed))
T["removed_types"] = ", ".join("%d %s%s" % (n, t, "s" if n != 1 else "") for t, n in removed_types.most_common()) or "none"
T["replaced_by"] = ", ".join("%s in %d" % (t, n) for t, n in replaced.most_common()) or "none"

# ---- houses with a high corridor score: where it came from
traces = []
for c in chains_of("H"):
    f, sc, L = final[(c, "H")]
    if sc["corridor_rooms"] >= 3:
        g = door_graph(L); start = entrance_rooms(L); base = _depths(g, start, None)
        cut = {x: sum(1 for o in base if o != x and o not in _depths(g, start, x)) for x in L.rooms if L.rooms[x].type in DESTINATIONS}
        x = max(cut, key=cut.get)
        steps_ok = [s for s in PATCHES if (c, s) in final and (c, chr(ord(s) - 1)) in final]
        jump = max(steps_ok, key=lambda s: final[(c, s)][1]["corridor_rooms"] - final[(c, chr(ord(s) - 1))][1]["corridor_rooms"])
        before = final[(c, chr(ord(jump) - 1))]
        lines = final[(c, jump)][0]["script"].strip().splitlines()
        removed_rooms = ["%s (a %s)" % (l.split()[2], before[2].rooms[l.split()[2]].type) for l in lines
                         if l.startswith("remove room") and l.split()[2] in before[2].rooms]
        traces.append("* Chain %d, score %d: the %s %s is the only way into %d other rooms. The largest rise came at step %s (from %d to %d), "
                      "with %d free cells before it; that step's script had %d commands and removed %s."
                      % (c, sc["corridor_rooms"], L.rooms[x].type, x, cut[x], jump, before[1]["corridor_rooms"],
                         final[(c, jump)][1]["corridor_rooms"], CELLS - len(before[2].rooms), len(lines), ", ".join(removed_rooms) or "no room"))
T["traces"] = "\n".join(traces) or "No stepwise-patched house has a corridor score of 3 or more."

# ---- script length, tokens and cost
rows = [("Agent", "Valid scripts", "Median commands", "Range", "Calls", "Output tokens per call", "of which thinking", "Cost (USD, list price)")]
per_call = {}
for name, steps in (("A (build 4 rooms)", "A"), ("B–H (add one room)", "".join(PATCHES)), ("I (build 11 rooms)", "I"), ("J (add 7 rooms)", "J")):
    n = [r["command_count"] for r in mine if label(r).step in steps and ok(r)]
    rs = [r for r in mine if label(r).step in steps]
    u = [r["agent_usage"] for r in rs]
    per_call[steps] = sum(x["output_tokens"] for x in u) / len(rs)
    rows.append((name, str(len(n)), "%.0f" % st.median(n), "%d–%d" % (min(n), max(n)), str(len(rs)), "{:,.0f}".format(per_call[steps]),
                 "{:.0%}".format(sum(x["thinking_tokens"] for x in u) / sum(x["output_tokens"] for x in u)), "%.2f" % sum(x["cost_usd"] for x in u)))
T["cost"] = md(rows)
T["cost_total"] = "%.2f" % sum(r["agent_usage"]["cost_usd"] for r in mine)
T["cost_chain"] = "%.2f" % (sum(r["agent_usage"]["cost_usd"] for r in mine) / 6)
T["seq_vs_planned"] = "%.1f" % (len(PATCHES) * per_call["".join(PATCHES)] / per_call["I"])

# ---- appendix
rows = [("Chain", "House") + NAMES]
for chain in range(1, 7):
    for step, name in ARMS:
        if (chain, step) in final:
            sc = final[(chain, step)][1]
            rows.append((str(chain), step, "%d" % sc["corridor_rooms"], "%.2f" % sc["privacy_order"], "%.2f" % sc["walking_distance"],
                         "%d" % sc["compactness"]))
        else:
            rows.append((str(chain), step, "no valid house", "", "", ""))
T["per_chain"] = md(rows)
example_chain = min(c for c in range(1, 7) if all((c, s) in final for s in "AHIJ"))
T["example_chain"] = str(example_chain)
ds = {s: Drawing("%s (chain %d)" % (s, example_chain), final[(example_chain, s)][2]) for s in "AHIJ"}
T["drawing_1"] = render_side_by_side([ds["A"], ds["H"]]).split("\n\nLegend:")[0]
T["drawing_2"] = render_side_by_side([ds["I"], ds["J"]]).split("\n\nLegend:")[0]
T["prompt"] = "\n".join(textwrap.fill(line, 78) if len(line) > 100 else line
                        for line in (ROOT / "house" / "prompt_template.txt").read_text().rstrip("\n").splitlines())

if __name__ == "__main__":
    text = (ROOT / "paper" / "REPORT.template.md").read_text()
    for key, value in T.items():
        text = text.replace("{{%s}}" % key, value)
    left = [k for k in re.findall(r"\{\{(\w+)\}\}", text) if k not in ("LAYOUT", "REQUEST")]
    assert not left, left
    (ROOT / "REPORT.md").write_text(text)
    print("wrote REPORT.md,", len(text.splitlines()), "lines,", len(text.split()), "words")
