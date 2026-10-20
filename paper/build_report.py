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
from house.commands import script_cost  # noqa: E402
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
                        for line in (ROOT / "paper" / "prompt_5x5_run.txt").read_text().rstrip("\n").splitlines())

# ---- second run: houses without hallways (only the counts the text uses; each claim in the text is checked here)
assert all(sum(r.type == "hallway" for r in final[k][2].rooms.values()) >= 3 for k in finals), "every first-run final house has several hallways"
def final_houses(runs, effort):
    """(chain, step) -> (record, scores, layout) of the last valid house, for a run where every step has one."""
    houses = {}
    for chain in range(1, 7):
        for step in STEPS:
            f = final_house(runs, Label("sonnet55", effort, chain, step))
            assert f, "every chain has a valid house at every step"
            houses[(chain, step)] = (f, scores_of(f), parse_layout(f["layout"]))
    return houses


def patch_steps(houses):
    """(chain, step, rooms removed, rooms before, share of the previous house unchanged) for every patch step."""
    out = []
    for c in range(1, 7):
        for step in PATCHES:
            prev, cur = houses[(c, chr(ord(step) - 1))], houses[(c, step)]
            gone = [l for l in cur[0]["script"].splitlines() if l.strip().startswith("remove room") and l.split()[2] in prev[2].rooms]
            out.append((c, step, len(gone), len(prev[2].rooms), same(prev[2], cur[2])))
    assert all(s[4] == 1 for s in out if s[2] == 0), "a step that removes no room keeps every room where it was"
    return out


nh = final_houses(load_runs(ROOT / "runs_no_hallways"), EFFORT)
nh_values = lambda step, score: [nh[(c, step)][1][score] for c in range(1, 7)]
assert all(x >= 3 for s in "HIJ" for x in nh_values(s, "corridor_rooms")), "every final house has a corridor score of 3 or more"
assert st.mean(nh_values("I", "corridor_rooms")) >= st.mean(nh_values("H", "corridor_rooms")), "planning found no fewer forced passages"
assert len({x for s in "HIJ" for x in nh_values(s, "privacy_order")}) == 1, "privacy order is the same in every final house"
assert min(perm_p(nh_values(p, s), nh_values("I", s)) for s in SCORES for p in "HJ") > 0.05, "no planned test comes near a difference"
corridor_path = [st.mean(nh_values(s, "corridor_rooms")) for s in "ABCDEFGH"]
assert all(b > a for a, b in zip(corridor_path, corridor_path[1:])), "corridor rooms rises with every patch step"
steps = patch_steps(nh)
rebuilds = [s for s in steps if s[2] == s[3]]
assert all(s[2] in (0, 1) for s in steps if s not in rebuilds), "a step removes no room, one room or every room"
T["nh_patch_steps"] = str(len(steps))
T["nh_attached"] = str(sum(1 for s in steps if s[2] == 0))
T["nh_one_room"] = str(sum(1 for s in steps if s[2] == 1))
T["nh_rebuilt"] = str(len(rebuilds))
T["nh_rebuilt_same"] = str(sum(1 for s in rebuilds if s[4] >= 0.5))
step_counts = Counter(s[1] for s in rebuilds)
top_step, top_n = step_counts.most_common(1)[0]
T["nh_rebuild_step"], T["nh_rebuild_step_n"] = top_step, str(top_n)
T["nh_rebuild_step_rooms"] = str(next(s[3] for s in rebuilds if s[1] == top_step))
rebuild_chains = sorted({s[0] for s in rebuilds})
attach_chains = [c for c in range(1, 7) if c not in rebuild_chains]
T["nh_rebuild_chains"], T["nh_attach_chains"] = str(len(rebuild_chains)), str(len(attach_chains))
assert st.mean(nh[(c, "H")][1]["corridor_rooms"] for c in rebuild_chains) >= st.mean(nh[(c, "H")][1]["corridor_rooms"] for c in attach_chains), \
    "chains that rebuilt ended no better than chains that only attached"
a_kept = [same(nh[(c, "A")][2], nh[(c, "H")][2]) for c in range(1, 7)]
T["nh_a_intact"] = str(sum(x == 1 for x in a_kept))
T["nh_a_quarter"] = str(sum(x <= 0.25 for x in a_kept))
T["nh_distinct_A"] = str(len({shape(nh[(c, "A")][2]) for c in range(1, 7)}))

# ---- third run: houses without hallways at low effort (as above: the counts the text uses, and its claims checked)
lo_runs = load_runs(ROOT / "runs_no_hallways_low")
lo = final_houses(lo_runs, "low")
lo_values = lambda step, score: [lo[(c, step)][1][score] for c in range(1, 7)]
assert all(ok(r) for r in lo_runs if parse_label(r["label"]).step in PATCHES), "no patch step failed"
assert st.mean(lo_values("H", "corridor_rooms")) <= st.mean(lo_values("I", "corridor_rooms")), "patched houses had no more forced passages"
assert len({x for s in "HIJ" for x in lo_values(s, "privacy_order")}) == 1, "privacy order is the same in every final house"
assert min(perm_p(lo_values(p, s), lo_values("I", s)) for s in SCORES for p in "HJ") > 0.05, "no planned test comes near a difference"
lo_steps = patch_steps(lo)
lo_attached, lo_rebuilt = sum(1 for s in lo_steps if s[2] == 0), sum(1 for s in lo_steps if s[2] == s[3])
assert lo_attached > int(T["nh_attached"]) and lo_rebuilt < int(T["nh_rebuilt"]), "the weaker agents patched more and rebuilt less"
T["lo_attached"], T["lo_rebuilt"] = str(lo_attached), str(lo_rebuilt)
T["lo_a_intact"] = str(sum(same(lo[(c, "A")][2], lo[(c, "H")][2]) == 1 for c in range(1, 7)))
T["lo_distinct_A"] = str(len({shape(lo[(c, "A")][2]) for c in range(1, 7)}))
loops = lambda layout: sum(len(v) for v in door_graph(layout).values()) // 2 - (len(layout.rooms) - 1)   # 0 for a tree
both = [(run, c, s) for run in (nh, lo) for c in range(1, 7) for s in "HIJ"]
not_trees = [(run, c, s) for run, c, s in both if loops(run[(c, s)][2]) > 0]
assert len(not_trees) == 1 and not_trees[0][0] is lo and not_trees[0][2] == "H", "one stepwise-patched low-effort house is not a tree"
run, c, s = not_trees[0]
assert loops(run[(c, s)][2]) == 1, "the house that is not a tree has one extra door"
assert run[(c, s)][1]["corridor_rooms"] < min(r[(k, t)][1]["corridor_rooms"] for r, k, t in both if (r, k, t) != not_trees[0]), \
    "the house that is not a tree has the fewest forced passages"
T["nh_lo_final"] = str(len(both))

# ---- building and demolishing cost: a run without hallways (one sentence of the text), and two runs with hallways
free_cost = final_houses(load_runs(ROOT / "runs_cost"), EFFORT)
assert all(s[2] == 0 for s in patch_steps(free_cost)), "without hallways, no costed patch step removed a room"
assert min(perm_p([free_cost[(c, p)][1][s] for c in range(1, 7)], [free_cost[(c, "I")][1][s] for c in range(1, 7)])
           for s in SCORES for p in "HJ") > 0.05, "without hallways, the cost did not make patching worse than planning"

COST_RUNS = (("Cost run", "runs_cost_hallways"), ("Repeat", "runs_cost_hallways_2"))
FIRST = "First run (no cost)"
cr = {name: (load_runs(ROOT / folder), final_houses(load_runs(ROOT / folder), EFFORT)) for name, folder in COST_RUNS}
houses_of = {FIRST: final, **{name: h for name, (_, h) in cr.items()}}
vals = lambda name, step, score: [houses_of[name][(c, step)][1][score] for c in range(1, 7)]
halls = lambda layout: sum(r.type == "hallway" for r in layout.rooms.values())
hall_vals = lambda name, step: [halls(houses_of[name][(c, step)][2]) for c in range(1, 7)]
cost_of = lambda name, c, step: script_cost(houses_of[name][(c, step)][0]["script"])
assert all((c, s) in final for c in range(1, 7) for s in STEPS), "the first run has a house at every step, to compare with"


def cause(r):
    if not r["accepted"]:
        e = r["errors"][0]["reason"]
        for key, name in (("cannot understand", "line outside the language"), ("already in use", "room id already in use"),
                          ("already taken", "cell already taken"), ("not an outer wall", "window on a wall that is not outer")):
            if key in e:
                return name
        return "other rejection"
    return "house broke rule %s" % ", ".join(str(n) for n in sorted({v["rule"] for v in r["violations"]}))


rows = [("Run", "Calls", "Failed", "Failed patch steps", "Failed planned builds", "Failed one-shot patches", "Causes")]
for name, (rs, _) in cr.items():
    rs = [r for r in rs if parse_label(r["label"])]
    bad = [r for r in rs if not ok(r)]
    of = lambda steps: "%d of %d" % (sum(1 for r in bad if parse_label(r["label"]).step in steps), sum(1 for r in rs if parse_label(r["label"]).step in steps))
    rows.append((name, str(len(rs)), str(len(bad)), of("".join(PATCHES)), of("I"), of("J"),
                 "; ".join("%s (%d)" % kv for kv in Counter(cause(r) for r in bad).most_common()) or "none"))
    assert not any(parse_label(r["label"]).step in "IJ" for r in bad), "no planned build or one-shot patch failed"
T["ch_completion"] = md(rows)

rows = [("Run", "House", "Corridor rooms", "Privacy order", "Walking distance", "Compactness", "Hallways (fewest–most)")]
for name in houses_of:
    for step, house in (("H", "H (patched step by step)"), ("I", "I (planned from scratch)"), ("J", "J (patched in one go)")):
        h = hall_vals(name, step)
        rows.append((name, house) + tuple(ms(vals(name, step, s)) for s in SCORES) + ("%d–%d" % (min(h), max(h)),))
T["ch_scores"] = md(rows)

names = [n for n, _ in COST_RUNS]
both_runs = lambda a, b: "%s in each run" % a if a == b else "%s in the cost run and %s in the repeat" % (a, b)
rows = [("Score", "Patched house") + tuple("%s: mean patched / planned, p" % n for n in names)]
ch_p = {}
for s, sname in zip(SCORES, NAMES):
    for patched, pname in (("H", "H step by step"), ("J", "J in one go")):
        cells = []
        for n in names:
            a, b = vals(n, patched, s), vals(n, "I", s)
            ch_p[(n, s, patched)] = perm_p(a, b)
            cells.append("%.2f / %.2f, %.3f%s" % (st.mean(a), st.mean(b), ch_p[(n, s, patched)], " (all equal)" if len(set(a + b)) == 1 else ""))
        rows.append((sname, pname) + tuple(cells))
T["ch_tests"] = md(rows)
for n in names:
    assert ch_p[(n, "corridor_rooms", "H")] < 0.05 / 8, "in each cost run, stepwise patching has more forced passages than planning"
    assert all(p > 0.05 / 8 for (m, s, h), p in ch_p.items() if m == n and (s, h) != ("corridor_rooms", "H")), "no other planned test passes"
T["ch_p_corridor"] = both_runs(*("%.3f" % ch_p[(n, "corridor_rooms", "H")] for n in names))

rows = [("Run", "Patched house", "Corridor ≥ 3 (patched)", "Corridor ≥ 3 (planned I)", "Fisher exact p", "Rank-sum exact p")]
for n in names:
    for patched, pname in (("H", "H step by step"), ("J", "J in one go")):
        a, b = vals(n, patched, "corridor_rooms"), vals(n, "I", "corridor_rooms")
        ka, kb = sum(x >= 3 for x in a), sum(x >= 3 for x in b)
        rows.append((n, pname, "%d of 6" % ka, "%d of 6" % kb, "%.3f" % fisher(ka, 6 - ka, kb, 6 - kb), "%.3f" % ranksum_p(a, b)))
    assert all(x >= 3 for x in vals(n, "H", "corridor_rooms")) and not any(any(vals(n, s, "corridor_rooms")) for s in "IJ"), \
        "every stepwise-patched house has a corridor score of 3 or more, every planned and one-shot house 0"
T["ch_corridor_tests"] = md(rows)

rows = [("Score", "House", "First run (no cost)") + tuple("%s, p against the first run" % n for n in names)]
vs_first = {}
for s, sname in zip(SCORES, NAMES):
    for step in "HIJ":
        cells = []
        for n in names:
            vs_first[(n, s, step)] = perm_p(vals(n, step, s), vals(FIRST, step, s))
            cells.append("%.2f, %.3f" % (st.mean(vals(n, step, s)), vs_first[(n, s, step)]))
        rows.append((sname, step, "%.2f" % st.mean(vals(FIRST, step, s))) + tuple(cells))
T["ch_vs_first"] = md(rows)
for n in names:
    assert vs_first[(n, "corridor_rooms", "H")] < 0.05 / 12, "the cost made the stepwise-patched houses worse than in the first run"
    assert all(vs_first[(n, s, step)] > 0.05 / 12 for s in SCORES for step in "IJ"), "the cost did not change the planned or one-shot houses"

rows = [("Run", "") + tuple("ABCDEFGH")]
for name in houses_of:
    path = [st.mean(vals(name, s, "corridor_rooms")) for s in "ABCDEFGH"]
    rows.append((name, "corridor rooms") + tuple("%.2f" % x for x in path))
    rows.append(("", "hallways") + tuple("%.1f" % st.mean(hall_vals(name, s)) for s in "ABCDEFGH"))
    if name != FIRST:
        assert all(b > a for a, b in zip(path, path[1:])), "with a cost, corridor rooms rises with every patch step"
T["ch_trajectory"] = md(rows)

rows = [("Run", "Patch steps", "Removed no room", "Removed one room", "Removed more", "Last step that removed a room", "Median cost of a patch script")]
last_removal = {}
for name in houses_of:
    steps_ = patch_steps(houses_of[name])
    removals = [s for s in steps_ if s[2] > 0]
    last_removal[name] = max(s[1] for s in removals)
    costs = [cost_of(name, s[0], s[1]) for s in steps_]
    rows.append((name, str(len(steps_)), str(sum(s[2] == 0 for s in steps_)), str(sum(s[2] == 1 for s in steps_)),
                 str(sum(s[2] > 1 for s in steps_)), last_removal[name], "%g" % st.median(costs)))
    if name != FIRST:
        assert all(s[2] <= 1 for s in steps_), "a costed patch step removes at most one room"
        for c, step, gone, before, kept in removals:
            prev, cur = houses_of[name][(c, chr(ord(step) - 1))], houses_of[name][(c, step)]
            assert all(cur[2].room_at(next(iter(prev[2].rooms[l.split()[2]].cells))).type == "hallway"
                       for l in cur[0]["script"].splitlines() if l.startswith("remove room")), "every costed refactoring made a hallway"
        assert sum(x == 5 for x in costs) > len(costs) / 2, "most costed patch steps cost exactly 5"
        assert max(hall_vals(name, "H")) < min(hall_vals(name, "I")), "every stepwise-patched house has fewer hallways than every planned house"
T["ch_patching"] = md(rows)
T["ch_removed_first"] = str(sum(s[2] > 0 for s in patch_steps(final)))
T["ch_removed"] = both_runs(*(str(sum(s[2] > 0 for s in patch_steps(houses_of[n]))) for n in names))
T["ch_last_removal"] = max(last_removal[n] for n in names)
hallway_path = lambda n: [st.mean(hall_vals(n, s)) for s in "ABCDEFGH"]
T["ch_last_hallway"] = max("ABCDEFGH"[i] for n in names for i in range(1, 8) if hallway_path(n)[i] != hallway_path(n)[i - 1])
assert all(hallway_path(n)["ABCDEFGH".index(T["ch_last_hallway"]):] == [hallway_path(n)[-1]] * (8 - "ABCDEFGH".index(T["ch_last_hallway"]))
           for n in names), "no costed patch step added a hallway after the last one named in the text"

rows = [("Run", "Stepwise route A to H", "Planned build I", "One-shot route A and J", "Chains where the stepwise route cost less than I")]
cheaper = 0
for name in houses_of:
    route = lambda steps: [sum(cost_of(name, c, s) for s in steps) for c in range(1, 7)]
    a, b, j = route("ABCDEFGH"), route("I"), route("AJ")
    n_cheaper = sum(x < y for x, y in zip(a, b))
    label_ = name if name != FIRST else "First run, priced the same"
    rows.append((label_,) + tuple("%.0f (%d–%d)" % (st.mean(v), min(v), max(v)) for v in (a, b, j)) + ("%d of 6" % n_cheaper,))
    if name != FIRST:
        cheaper += n_cheaper
        assert all(x < y for x, y in zip(a, j)), "a costed stepwise route always cost less than the one-shot route"
        assert max(a) < min(route_first for route_first in [sum(cost_of(FIRST, c, s) for s in "ABCDEFGH") for c in range(1, 7)]), \
            "every costed stepwise route cost less than any first-run stepwise route, priced the same"
T["ch_routes"] = md(rows)
T["ch_cheaper"] = str(cheaper)                 # cheaper than I, and always cheaper than A and J: the cheapest of the three
T["ch_money"] = both_runs(*("%.2f USD" % sum(r["agent_usage"]["cost_usd"] for r in cr[n][0] if parse_label(r["label"])) for n in names))
T["ch_calls"] = both_runs(*(str(sum(1 for r in cr[n][0] if parse_label(r["label"]))) for n in names))
T["ch_distinct_A"] = both_runs(*(str(len({shape(houses_of[n][(c, "A")][2]) for c in range(1, 7)})) for n in names))

rows = [("Run", "Chain", "House", "Corridor rooms", "Privacy order", "Walking distance", "Compactness", "Hallways", "Cost of the script")]
for n in names:
    for c in range(1, 7):
        for step in "HIJ":
            sc = houses_of[n][(c, step)][1]
            rows.append((n, str(c), step, "%d" % sc["corridor_rooms"], "%.2f" % sc["privacy_order"], "%.2f" % sc["walking_distance"],
                         "%d" % sc["compactness"], str(halls(houses_of[n][(c, step)][2])), str(cost_of(n, c, step))))
T["ch_per_chain"] = md(rows)
h_run1 = vals(names[0], "H", "corridor_rooms")
ch_example = min(range(1, 7), key=lambda c: (abs(h_run1[c - 1] - st.median(h_run1)), c))
T["ch_example_chain"] = str(ch_example)
d = [Drawing("%s (chain %d)" % (s, ch_example), houses_of[names[0]][(ch_example, s)][2]) for s in "HI"]
T["ch_drawing"] = render_side_by_side(d).split("\n\nLegend:")[0]
T["ch_prompt"] = "\n".join(textwrap.fill(line, 78) if len(line) > 100 else line
                           for line in (ROOT / "house" / "prompt_template_hallways.txt").read_text().rstrip("\n").splitlines())


WORDS = {str(n): w for n, w in enumerate("no one two three four five six seven eight nine ten".split())}
for key in ("nh_rebuilt_same", "nh_rebuild_step_n", "nh_rebuild_step_rooms", "nh_rebuild_chains", "nh_attach_chains", "nh_a_intact",
            "nh_a_quarter", "nh_one_room", "lo_a_intact"):
    T[key] = WORDS.get(T[key], T[key])


if __name__ == "__main__":
    text = (ROOT / "paper" / "REPORT.template.md").read_text()
    for key, value in T.items():
        text = text.replace("{{%s}}" % key, value)
    left = [k for k in re.findall(r"\{\{(\w+)\}\}", text) if k not in ("LAYOUT", "REQUEST")]
    assert not left, left
    (ROOT / "REPORT.md").write_text(text)
    print("wrote REPORT.md,", len(text.splitlines()), "lines,", len(text.split()), "words")
