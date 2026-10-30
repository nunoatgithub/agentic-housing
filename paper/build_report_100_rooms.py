"""Builds REPORT_100_rooms.md from paper/REPORT_100_rooms.template.md and the saved runs of houses of 70 to 100 rooms.

    python paper/build_report_100_rooms.py

Every number in the report is computed here from the saved records in runs_100_rooms/ and runs_100_rooms_no_hallways/,
and every claim the text makes about them is checked here. The runs are described, not tested.
"""
import json
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from house.layout_format import parse_layout  # noqa: E402
from house.model import set_grid_size  # noqa: E402
from house.scores import score  # noqa: E402

set_grid_size(15)
SCORES = ("corridor_rooms", "privacy_order", "walking_distance", "compactness")
NAMES = ("Corridor rooms", "Privacy order", "Walking distance", "Compactness")
DIGITS = {"corridor_rooms": 0, "privacy_order": 4, "walking_distance": 2, "compactness": 0}
MODELS = {"sonnet55": "Sonnet 5.5", "gpt6luna": "GPT-6 Luna"}
KINDS = (("step", "One room at a time"), ("all", "All at once"))
LABEL = re.compile(r"^(\w+)-(\w+)-h(\d+)-c(\d+)-(step|all)(\d+)$")
ALONG = (0, 5, 10, 15, 20, 25, 30)          # the steps the along-the-chain tables show
LAST_ALL = 28                                # the last step an all-at-once call starts from
T = {}


def md(rows):
    """A markdown table whose pipes line up in the source."""
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    line = lambda r: "| " + " | ".join(c.ljust(w) for c, w in zip(r, widths)) + " |"
    return "\n".join([line(rows[0]), "| " + " | ".join("-" * w for w in widths) + " |"] + [line(r) for r in rows[1:]])


def fmt(value, name):
    return "%.*f" % (DIGITS[name], value)


def words(n):
    return ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")[n] if n <= 10 else str(n)


def key(layout):
    """The rooms of a house as (cells, type): a room that keeps its cells and type is the same room, whatever its id."""
    return {(tuple(sorted(r.cells)), r.type) for r in layout.rooms.values()}


class Run:
    """The saved records of one run folder, and every agent call's starting and resulting house."""

    def __init__(self, folder):
        self.folder = folder
        self.records = [json.loads(p.read_text()) for p in sorted((ROOT / folder).glob("run_*.json"))]
        self.seeds = {h: parse_layout((ROOT / folder / "seeds" / ("house%d.txt" % h)).read_text()) for h in range(1, 5)}
        self.calls = defaultdict(dict)       # (model, house, chain) -> {(kind, step): the valid record}
        for r in self.records:
            m = LABEL.match(r["label"])
            if r["accepted"] and r["valid"]:
                self.calls[(m[1], int(m[3]), int(m[4]))][(m[5], int(m[6]))] = r
        self.chains = sorted(self.calls, key=lambda c: (list(MODELS).index(c[0]), c[2]))
        self._layouts = {}

    def layout(self, chain, kind, step):
        k = (chain, kind, step)
        if k not in self._layouts:
            self._layouts[k] = parse_layout(self.calls[chain][(kind, step)]["layout"])
        return self._layouts[k]

    def start(self, chain, kind, step):
        """The house a call started from: the seed house, or the house the one-room step before it left."""
        before = step - 1 if kind == "step" else step
        return self.seeds[chain[1]] if before == 0 else self.layout(chain, "step", before)

    def scores(self, chain, kind, step):
        r = self.calls[chain].get((kind, step))
        return r["scores"] if r else None

    def changes(self, model, kind):
        """Per call of this model and kind: (rooms gone from the house it started from, its size, hallways added,
        doors added, rooms added, chain, step)."""
        out = []
        for chain in self.chains:
            if chain[0] != model:
                continue
            for (k, step) in sorted(self.calls[chain]):
                if k != kind:
                    continue
                a, b = self.start(chain, k, step), self.layout(chain, k, step)
                ka, kb = key(a), key(b)
                halls = lambda L: sum(r.type == "hallway" for r in L.rooms.values())
                out.append((len(ka - kb), len(ka), halls(b) - halls(a), len(b.doors - a.doors), len(kb - ka), chain, step))
        return out

    def tries(self, model, kind):
        """Every try of this model and kind, by outcome."""
        out = Counter()
        for r in self.records:
            m = LABEL.match(r["label"])
            if m[1] != model or m[5] != kind:
                continue
            out["valid" if r["accepted"] and r["valid"] else "cut off" if r.get("cut_off") else "rejected" if not r["accepted"] else "invalid"] += 1
        return out

    def usage(self, model, kind, field):
        out = []
        for r in self.records:
            m = LABEL.match(r["label"])
            u = r.get("agent_usage") or {}
            if m[1] == model and m[5] == kind and u.get(field) is not None:
                out.append(u[field])
        return out


def chain_name(chain):
    return "house %d, chain %d (%s)" % (chain[1], chain[2], MODELS[chain[0]])


def final_table(run, models):
    rows = [("Seed house", "Chain", "Model", "House") + NAMES]
    for h in range(1, 5):
        seed = vars(score(run.seeds[h]))
        rows.append((str(h), "", "", "seed house (70 rooms)") + tuple(fmt(seed[s], s) for s in SCORES))
        for chain in run.chains:
            if chain[1] != h or chain[0] not in models:
                continue
            for kind, step, name in (("step", 30, "after step 30"), ("all", 0, "all at once from step 0"), ("all", 15, "all at once from step 15")):
                sc = run.scores(chain, kind, step)
                rows.append(("", str(chain[2]), MODELS[chain[0]], name) + (tuple(fmt(sc[s], s) for s in SCORES) if sc else ("–",) * 4))
    return md(rows)


def along_tables(run):
    out = []
    for s, name in zip(SCORES, NAMES):
        rows = [("Chain", "Seed house", "Model", "House") + tuple("step %d" % k for k in ALONG)]
        for chain in run.chains:
            for kind, kname in (("step", "after the step"), ("all", "all at once from the step")):
                cells = []
                for k in ALONG:
                    sc = (vars(score(run.seeds[chain[1]])) if (kind, k) == ("step", 0) else
                          run.scores(chain, kind, k) if kind == "step" or k <= LAST_ALL else None)
                    cells.append(fmt(sc[s], s) if sc else "–")
                rows.append((str(chain[2]), str(chain[1]), MODELS[chain[0]], kname) + tuple(cells))
        out.append("**%s**\n\n%s" % (name, md(rows)))
    return "\n\n".join(out)


def change_table(run, models, hallways):
    head = ("Model", "Agent", "Calls", "Calls that removed a room", "Most rooms removed by one call", "Least share of the house kept")
    rows = [head + (("Hallways added per call",) if hallways else ())]
    for model in models:
        for kind, kname in KINDS:
            ch = run.changes(model, kind)
            rows.append((MODELS[model], kname, str(len(ch)), str(sum(1 for c in ch if c[0])), str(max(c[0] for c in ch)),
                         "%.1f%%" % (100 * min(1 - c[0] / c[1] for c in ch)))
                        + (("%.2f" % st.mean(c[2] for c in ch),) if hallways else ()))
    return md(rows)


def tries_table(run, models):
    rows = [("Model", "Agent", "Tries", "Valid", "Script rejected", "House invalid", "Reply cut off", "Output tokens per try", "Cost per try")]
    for model in models:
        for kind, kname in KINDS:
            t, tok, cost = run.tries(model, kind), run.usage(model, kind, "output_tokens"), run.usage(model, kind, "cost_usd")
            rows.append((MODELS[model], kname, str(sum(t.values())), str(t["valid"]), str(t["rejected"]), str(t["invalid"]), str(t["cut off"]),
                         "%d" % st.mean(tok) if tok else "not reported", "$%.3f" % st.mean(cost) if cost else "not reported"))
    return md(rows)


# ---- run 1: hallways free
r1 = Run("runs_100_rooms")
S1 = [c for c in r1.chains]
assert all(c[0] == "sonnet55" for c in S1) and len(S1) == 4, "run 1 has four Sonnet chains, one per seed house"
assert all(len(r1.calls[c]) == 59 for c in S1), "every run 1 chain has all 59 calls"
T["r1_final"] = final_table(r1, ["sonnet55"])
T["r1_changes"] = change_table(r1, ["sonnet55"], hallways=True)
T["r1_tries"] = tries_table(r1, ["sonnet55"])
T["r1_along"] = along_tables(r1)
seed_sc = {h: vars(score(r1.seeds[h])) for h in range(1, 5)}
step30 = {c[1]: r1.scores(c, "step", 30) for c in S1}
all00 = {c[1]: r1.scores(c, "all", 0) for c in S1}
assert all(step30[h]["corridor_rooms"] > all00[h]["corridor_rooms"] for h in range(1, 5)), "run 1: corridor rooms worse after step 30 in every house"
assert all(step30[h]["walking_distance"] < all00[h]["walking_distance"] for h in range(1, 5)), "run 1: walking distance better after step 30 in every house"
T["r1_compact_better"] = words(sum(step30[h]["compactness"] < all00[h]["compactness"] for h in range(1, 5)))
assert all(abs(all00[h]["corridor_rooms"] - seed_sc[h]["corridor_rooms"]) <= 1 for h in range(1, 5)), \
    "run 1: all at once from step 0 left corridor rooms where the seed house had it (within one)"
assert all(all00[h]["corridor_rooms"] >= seed_sc[h]["corridor_rooms"] for h in range(1, 5)), "run 1: no all-at-once house from step 0 had fewer corridor rooms than its seed house"
T["r1_all00_same_corridor"] = words(sum(all00[h]["corridor_rooms"] == seed_sc[h]["corridor_rooms"] for h in range(1, 5)))
privacy_100 = {(h, sc["privacy_order"]) for run, chains in ((r1, S1),) for c in chains for (k, s), r in run.calls[c].items()
               if k == "all" or s == 30 for h, sc in ((c[1], r["scores"]),)}
assert len({p for h, p in privacy_100 if h in (1, 2)}) == 1 and len({p for h, p in privacy_100 if h in (3, 4)}) == 1, \
    "run 1: every 100-room house of a seed house has the same privacy order"
r1_step, r1_all = r1.changes("sonnet55", "step"), r1.changes("sonnet55", "all")
assert max(c[0] for c in r1_step) == 1 and max(c[0] for c in r1_all) <= 3, "run 1: no call removed more than three rooms"
T["r1_step_hall"], T["r1_all_hall"] = "%.2f" % st.mean(c[2] for c in r1_step), "%.2f" % st.mean(c[2] for c in r1_all)
T["r1_all_kept"] = "%.1f%%" % (100 * min(1 - c[0] / c[1] for c in r1_all))
T["r1_versions"] = ", ".join(sorted({r["claude_code"].split()[0] for r in r1.records}))

# ---- run 2: no hallway can be built
r2 = Run("runs_100_rooms_no_hallways")
S2 = [c for c in r2.chains if c[0] == "sonnet55"]
L2 = [c for c in r2.chains if c[0] == "gpt6luna"]
assert len(S2) == 8 and len(L2) == 4, "run 2 has eight Sonnet chains and four GPT-6 Luna chains"
missing = [(c, (k, s)) for c in r2.chains for k, s in [("all", i) for i in range(LAST_ALL + 1)] + [("step", i) for i in range(1, 31)]
           if (k, s) not in r2.calls[c]]
assert len(missing) == 1 and missing[0][0][0] == "gpt6luna", "run 2: one call has no valid house, in a GPT-6 Luna chain"
(mc, (mk, ms_)) = missing[0]
T["r2_missing"] = "the all-at-once call from step %d in %s" % (ms_, chain_name(mc))
T["r2_final_sonnet"] = final_table(r2, ["sonnet55"])
T["r2_final_luna"] = final_table(r2, ["gpt6luna"])
T["r2_changes"] = change_table(r2, ["sonnet55", "gpt6luna"], hallways=False)
T["r2_tries"] = tries_table(r2, ["sonnet55", "gpt6luna"])
T["r2_along"] = along_tables(r2)
s2_step, s2_all = r2.changes("sonnet55", "step"), r2.changes("sonnet55", "all")
assert not any(c[0] for c in s2_all), "run 2: no Sonnet all-at-once call removed a room"
gone = [c for c in s2_step if c[0]]
assert all(c[0] == 1 and c[5][1] in (3, 4) for c in gone), "run 2: Sonnet one-room steps removed at most one room, and only in houses 3 and 4"
gone_types = [next(r.type for r in r2.start(c[5], "step", c[6]).rooms.values() if (tuple(sorted(r.cells)), r.type) not in key(r2.layout(c[5], "step", c[6])))
              for c in gone]
T["r2_sonnet_gone_hallways"] = words(gone_types.count("hallway"))
assert set(gone_types) <= {"hallway", "bathroom"} and gone_types.count("bathroom") == 1, "run 2: the Sonnet steps removed seed hallways and one bathroom"
T["r2_sonnet_removing_steps"] = words(len(gone))
T["r2_sonnet_steps"] = str(len(s2_step))
s2_extra = [c[3] - c[4] for c in s2_step]
assert max(s2_extra) <= 1, "run 2: no Sonnet one-room step added more than one door beyond the doors of its new room"
l2_step, l2_all = r2.changes("gpt6luna", "step"), r2.changes("gpt6luna", "all")
rewired = [c for c in l2_step + l2_all if c[3] - c[4] >= 10]
T["r2_luna_rewired"] = words(len(rewired))
T["r2_luna_rewired_all"] = words(sum(1 for c in rewired if c in l2_all))
T["r2_luna_rewired_kept"] = words(sum(1 for c in rewired if c[0] == 0))
T["r2_luna_calls"] = str(len(l2_step) + len(l2_all))
big = max(l2_step, key=lambda c: c[3] - c[4])
T["r2_luna_big_doors"], T["r2_luna_big_where"] = str(big[3]), "step %d of %s" % (big[6], chain_name(big[5]))
before, after = r2.scores(big[5], "step", big[6] - 1), r2.scores(big[5], "step", big[6])
assert big[0] == 0 and after["corridor_rooms"] < before["corridor_rooms"] / 4, "the biggest rewiring removed no room and cut corridor rooms to under a quarter"
T["r2_luna_big_before"], T["r2_luna_big_after"] = str(before["corridor_rooms"]), str(after["corridor_rooms"])
rebuilt = [c for c in l2_step + l2_all if c[0] / c[1] >= 0.25]
T["r2_luna_rebuilt"] = words(len(rebuilt))
T["r2_luna_rebuilt_steps"] = words(sum(1 for c in rebuilt if c in l2_step))
assert all(c[5][1] in (1, 2) for c in rebuilt), "every GPT-6 Luna call that removed a quarter of the house or more was in a budget house"
step_redesigns = [c for c in l2_step if c in rewired or c in rebuilt]
assert sorted(c[5][1] for c in step_redesigns) == [1, 2] and len({c[6] for c in step_redesigns}) == 1, \
    "GPT-6 Luna redesigned by a one-room step once in each budget house, at the same step"
T["r2_luna_redesign_step"] = str(step_redesigns[0][6])
s2_final = {h: [r2.scores(c, "step", 30)["corridor_rooms"] for c in S2 if c[1] == h] for h in range(1, 5)}
l2_final = {c[1]: r2.scores(c, "step", 30)["corridor_rooms"] for c in L2}
assert all(l2_final[h] < seed_sc[h]["corridor_rooms"] < min(s2_final[h]) for h in (1, 2)), \
    "run 2, budget houses: GPT-6 Luna ended below the seed house's corridor rooms, every Sonnet chain above it"
assert all(min(s2_final[h]) > seed_sc[h]["corridor_rooms"] and l2_final[h] > seed_sc[h]["corridor_rooms"] for h in (3, 4)), \
    "run 2, planned houses: every chain ended above the seed house's corridor rooms"
for tag, chains in (("s", S2), ("l", L2)):          # after step 30 against all at once from step 0, chain by chain
    for name in ("corridor_rooms", "walking_distance"):
        pairs = [(r2.scores(c, "step", 30)[name], r2.scores(c, "all", 0)[name]) for c in chains]
        T["r2_%s_%s_lower" % (tag, name[:4])] = words(sum(a < b for a, b in pairs))
        T["r2_%s_%s_higher" % (tag, name[:4])] = words(sum(a > b for a, b in pairs))
assert all(T["r2_s_%s_%s" % (n, d)] != "no" for n in ("corr", "walk") for d in ("lower", "higher")), \
    "run 2: for Sonnet, neither kind of house came out consistently better on corridor rooms or walking distance"
T["r2_s_chains"], T["r2_l_chains"] = words(len(S2)), words(len(L2))
T["r2_s_versions"] = ", ".join(sorted({(r.get("agent_version") or r["claude_code"]).split()[0] for r in r2.records if r["label"].startswith("sonnet55")}))
T["r2_l_version"] = sorted({r["agent_version"].split("\n")[0].rstrip(".") for r in r2.records if r["label"].startswith("gpt6luna")})[0]

for k in ("r1_versions", "r2_s_versions"):
    assert re.fullmatch(r"[0-9., ]+", T[k]), k

if __name__ == "__main__":
    text = (ROOT / "paper" / "REPORT_100_rooms.template.md").read_text()
    unused = set(T) - set(re.findall(r"{{(\w+)}}", text))
    assert not unused, "computed but not in the template: %s" % sorted(unused)
    text = re.sub(r"{{(\w+)}}", lambda m: T[m.group(1)], text)
    assert "{{" not in text, "a placeholder has no value"
    (ROOT / "REPORT_100_rooms.md").write_text(text)
    print("wrote REPORT_100_rooms.md,", len(text.splitlines()), "lines,", len(text.split()), "words")
