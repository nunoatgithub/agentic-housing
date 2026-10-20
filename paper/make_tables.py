"""Every number in REPORT.md, computed from the saved runs.   python paper/make_tables.py [runs_dir]"""
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from house.experiment import PATCHES, STEPS, Label, final_house, load_runs, parse_label, scores_of  # noqa: E402
from house.layout_format import parse_layout  # noqa: E402

SCORES = ("corridor_rooms", "privacy_order", "walking_distance", "compactness")
runs = load_runs(Path(sys.argv[1] if len(sys.argv) > 1 else "runs"))
efforts = ("medium", "high")
arm_steps = {"patched step by step (H)": "H", "planned (I)": "I", "patched in one go (J)": "J"}


def ms(values):
    return "%.2f ± %.2f" % (st.mean(values), st.stdev(values)) if len(values) > 1 else ("%.2f" % values[0] if values else "-")


print("## calls and failures")
for effort in efforts:
    mine = [r for r in runs if parse_label(r["label"]) and parse_label(r["label"]).effort == effort]
    bad = [r for r in mine if not (r["accepted"] and r["valid"])]
    kinds = Counter("rejected" if not r["accepted"] else "invalid rule " + "+".join(str(n) for n in sorted({v["rule"] for v in r["violations"]})) for r in bad)
    print(effort, "calls", len(mine), "failed", len(bad), dict(kinds))
    for name, steps in (("patch steps B-H", PATCHES), ("A", ("A",)), ("I", ("I",)), ("J", ("J",))):
        rs = [r for r in mine if parse_label(r["label"]).step in steps]
        ok_first = sum(1 for r in rs if r["accepted"] and r["valid"])
        print("   ", name, "calls", len(rs), "valid", ok_first, "failed", len(rs) - ok_first)
    for chain in range(1, 7):
        have = "".join(s if final_house(runs, Label("sonnet55", effort, chain, s)) else "." for s in STEPS)
        print("    chain", chain, have)

print("\n## scores of the final house of each arm, per chain")
data = defaultdict(dict)       # (effort, arm step) -> chain -> scores
rooms = defaultdict(dict)
for effort in efforts:
    for step in ("A",) + tuple(arm_steps.values()):
        for chain in range(1, 7):
            f = final_house(runs, Label("sonnet55", effort, chain, step))
            if f:
                data[(effort, step)][chain] = scores_of(f)
                L = parse_layout(f["layout"])
                rooms[(effort, step)][chain] = Counter(r.type for r in L.rooms.values())
for effort in efforts:
    print("\n", effort)
    for score in SCORES:
        print(" ", score)
        for step in ("A",) + tuple(arm_steps.values()):
            vals = [data[(effort, step)][c][score] for c in sorted(data[(effort, step)])]
            per = " ".join("%s" % (round(v, 2)) for v in vals)
            print("    %s  n=%d  mean±sd %s   per chain: %s" % (step, len(vals), ms(vals), per))

print("\n## how many chains the patched house was lower / equal / higher than the planned house (chains with both)")
for effort in efforts:
    for patched in ("H", "J"):
        for score in SCORES:
            both = [c for c in range(1, 7) if c in data[(effort, patched)] and c in data[(effort, "I")]]
            lo = sum(data[(effort, patched)][c][score] < data[(effort, "I")][c][score] - 1e-9 for c in both)
            hi = sum(data[(effort, patched)][c][score] > data[(effort, "I")][c][score] + 1e-9 for c in both)
            print(effort, patched, "vs I", score, "n=%d" % len(both), "patched lower(better)", lo, "equal", len(both) - lo - hi, "patched higher(worse)", hi)

print("\n## mean score by step along the patch chain (A..H), per effort")
for effort in efforts:
    print(effort)
    for score in SCORES:
        row = []
        for step in "ABCDEFGH":
            vals = []
            for chain in range(1, 7):
                f = final_house(runs, Label("sonnet55", effort, chain, step))
                if f:
                    vals.append(scores_of(f)[score])
            row.append("%s:%.2f(n%d)" % (step, st.mean(vals), len(vals)) if vals else step + ":-")
        print("  ", score, " ".join(row))

print("\n## hallways and rooms in the final houses")
for effort in efforts:
    for step in ("A", "H", "I", "J"):
        h = [rooms[(effort, step)][c]["hallway"] for c in sorted(rooms[(effort, step)])]
        n = [sum(rooms[(effort, step)][c].values()) for c in sorted(rooms[(effort, step)])]
        print(effort, step, "hallways", h, "mean %.2f" % st.mean(h), "| rooms", n, "mean %.2f" % st.mean(n))

print("\n## tokens and cost")
for effort in efforts:
    mine = [r for r in runs if r.get("agent_usage") and parse_label(r["label"]) and parse_label(r["label"]).effort == effort]
    def tot(rs):
        u = [r["agent_usage"] for r in rs]
        return (len(rs), sum(x["input_tokens"] + x["cache_creation_input_tokens"] + x["cache_read_input_tokens"] for x in u),
                sum(x["output_tokens"] for x in u), sum(x["thinking_tokens"] for x in u), sum(x["cost_usd"] for x in u))
    print(effort, "all calls: calls %d input %d output %d thinking %d cost %.3f" % tot(mine))
    for name, steps in (("A", ("A",)), ("patch B-H", PATCHES), ("I", ("I",)), ("J", ("J",))):
        rs = [r for r in mine if parse_label(r["label"]).step in steps]
        print("   ", name, "calls %d input %d output %d thinking %d cost %.3f" % tot(rs))
    print("    per chain: cost %.3f" % (tot(mine)[4] / 6))
print("no usage recorded for", sum(1 for r in runs if not r.get("agent_usage")), "calls")
