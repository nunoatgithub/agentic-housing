"""Builds REPORT_100_rooms.md from paper/REPORT_100_rooms.template.md and the saved runs of houses of 70 to 100 rooms.

    python paper/build_report_100_rooms.py

Every number in the report is computed here from the saved records of the five runs (runs_100_rooms/,
runs_100_rooms_no_hallways/, runs_100_rooms_refactor/, runs_100_rooms_refactor_cost/ and runs_100_rooms_cost/), and every
claim the text makes about them is checked here. The runs are described, not tested.
"""
import hashlib
import json
import pickle
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
CACHE = ROOT / "paper" / ".report_cache"     # what each call's layout gives the report, so a rebuild parses nothing it has seen
SCORES = ("corridor_rooms", "privacy_order", "walking_distance", "compactness")
NAMES = ("Corridor rooms", "Privacy order", "Walking distance", "Compactness")
DIGITS = {"corridor_rooms": 0, "privacy_order": 4, "walking_distance": 2, "compactness": 0}
MODELS = {"sonnet55": "Sonnet 5.5", "opus55": "Opus 5.5", "gpt6luna": "GPT-6 Luna", "deepseekflash": "DeepSeek adapter, low"}
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


def and_list(values):
    values = list(values)
    return values[0] if len(values) == 1 else ", ".join(values[:-1]) + " and " + values[-1]


def share(change):
    """The share of the house a call received that is gone from its own house (removed or replaced)."""
    return change[0] / change[1]


def pct(value):
    return "%.0f%%" % (100 * value)


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
        self._seed_scores = {}
        self._seed_derived = {}
        self._derived = {}
        self._cache_file = CACHE / (folder + ".pkl")
        self._cache = pickle.loads(self._cache_file.read_bytes()) if self._cache_file.exists() else {}
        self._dirty = False
        self._changes = {}

    def seed_score(self, house):
        """The scores of a seed house, computed once: scoring a 70-room house compares every pair of rooms."""
        if house not in self._seed_scores:
            self._seed_scores[house] = vars(score(self.seeds[house]))
        return self._seed_scores[house]

    @staticmethod
    def derive(layout):
        """What the report takes from a house: its rooms as (cells, type), how many hallways it has, its doors."""
        return key(layout), sum(r.type == "hallway" for r in layout.rooms.values()), frozenset(layout.doors)

    def derived(self, chain, kind, step):
        """derive() of the house a call left, from the cache on disk when its layout is unchanged."""
        k = (chain, kind, step)
        if k not in self._derived:
            r = self.calls[chain][(kind, step)]
            token = (r["run_id"], hashlib.md5(r["layout"].encode()).hexdigest())
            hit = self._cache.get(r["run_id"])
            if hit is None or hit[0] != token:
                hit = (token, self.derive(self.layout(chain, kind, step)))
                self._cache[r["run_id"]] = hit
                self._dirty = True
            self._derived[k] = hit[1]
        return self._derived[k]

    def start_derived(self, chain, kind, step):
        before = step - 1 if kind == "step" else step
        if before == 0:
            if chain[1] not in self._seed_derived:
                self._seed_derived[chain[1]] = self.derive(self.seeds[chain[1]])
            return self._seed_derived[chain[1]]
        return self.derived(chain, "step", before)

    def keys(self, chain, kind, step):
        return self.derived(chain, kind, step)[0]

    def start_keys(self, chain, kind, step):
        return self.start_derived(chain, kind, step)[0]

    def save_cache(self):
        if self._dirty:
            CACHE.mkdir(exist_ok=True)
            self._cache_file.write_bytes(pickle.dumps(self._cache))

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
        doors added, rooms added, chain, step); computed once per model and kind."""
        if (model, kind) in self._changes:
            return self._changes[(model, kind)]
        out = []
        for chain in self.chains:
            if chain[0] != model:
                continue
            for (k, step) in sorted(self.calls[chain]):
                if k != kind:
                    continue
                (ka, ha, da), (kb, hb, db) = self.start_derived(chain, k, step), self.derived(chain, k, step)
                out.append((len(ka - kb), len(ka), hb - ha, len(db - da), len(kb - ka), chain, step))
        self._changes[(model, kind)] = out
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
        if not any(c[1] == h and c[0] in models for c in run.chains):
            continue
        seed = run.seed_score(h)
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
                    sc = (run.seed_score(chain[1]) if (kind, k) == ("step", 0) else
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


def by_chain(run, model, kind):
    """The calls of this model and kind, chain by chain, in house order."""
    out = defaultdict(list)
    for c in run.changes(model, kind):
        out[c[5]].append(c)
    return [out[chain] for chain in sorted(out, key=lambda ch: ch[1])]


def refactoring(run, model, kind):
    """Per chain, in house order: how many calls of this kind removed or replaced 10% or more of the house."""
    return [sum(share(c) >= 0.1 for c in calls) for calls in by_chain(run, model, kind)]


def most_refactored(run, model):
    return max(share(c) for kind, _ in KINDS for c in run.changes(model, kind))


# ---- run 1: hallways free
r1 = Run("runs_100_rooms")
S1 = [c for c in r1.chains if c[0] == "sonnet55"]
D1 = [c for c in r1.chains if c[0] == "deepseekflash"]
assert sorted(c[1] for c in S1) == [1, 2, 3, 4], "run 1 has four Sonnet chains, one per seed house"
assert sorted((c[1], c[2]) for c in D1) == [(1, 5), (3, 7)], "run 1 has DeepSeek chains for houses 1 and 3"
assert all(len(r1.calls[c]) == 59 for c in S1 + D1), "every run 1 chain has all 59 calls"
T["r1_final"] = final_table(r1, ["sonnet55"])
T["r1_final_deepseek"] = final_table(r1, ["deepseekflash"])
T["r1_changes"] = change_table(r1, ["sonnet55", "deepseekflash"], hallways=True)
T["r1_tries"] = tries_table(r1, ["sonnet55", "deepseekflash"])
T["r1_along"] = along_tables(r1)
seed_sc = {h: r1.seed_score(h) for h in range(1, 5)}
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
T["r1_versions"] = ", ".join(sorted({r["claude_code"].split()[0] for r in r1.records if r["label"].startswith("sonnet55")}))
assert all(r1.scores(c, k, s)["corridor_rooms"] == 0 for c in D1 for k, s in (("step", 30), ("all", 0))), \
    "run 1: the DeepSeek houses after step 30 and all at once from step 0 have corridor rooms 0"
d1_step, d1_all = r1.changes("deepseekflash", "step"), r1.changes("deepseekflash", "all")
T["r1_d_step_calls"] = str(len(d1_step))
T["r1_d_step_removed"] = words(sum(1 for c in d1_step if c[0]))
assert refactoring(r1, "deepseekflash", "step") == [1, 1], "run 1: one DeepSeek one-room step in each house removed 10% or more"
assert all(max(share(c) for c in calls) > 0.5 for calls in by_chain(r1, "deepseekflash", "step")), \
    "run 1: that DeepSeek one-room step removed more than half of the house"
T["r1_d_step_most"] = pct(max(share(c) for c in d1_step))
T["r1_d_all_big"] = and_list(str(n) for n in refactoring(r1, "deepseekflash", "all"))
T["r1_d_all_first"] = and_list(pct(share(calls[0])) for calls in by_chain(r1, "deepseekflash", "all"))
assert all(calls[0][6] == 0 and share(calls[0]) >= 0.1 for calls in by_chain(r1, "deepseekflash", "all")), \
    "run 1: the first DeepSeek all-at-once call in each house removed 10% or more"
T["r1_d_step_hall"], T["r1_d_all_hall"] = "%.2f" % st.mean(c[2] for c in d1_step), "%.2f" % st.mean(c[2] for c in d1_all)
assert max(share(c) for c in r1_step + r1_all) < 0.1, "run 1: no Sonnet call removed 10% or more of the house"

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
assert big[0] == 0 and after["corridor_rooms"] > before["corridor_rooms"], "the biggest rewiring removed no room and raised corridor rooms"
corridor_change = lambda c: (score(r2.start(c[5], "step" if c in l2_step else "all", c[6])).corridor_rooms,
                             r2.scores(c[5], "step" if c in l2_step else "all", c[6])["corridor_rooms"])
T["r2_luna_big_before"], T["r2_luna_big_after"] = str(before["corridor_rooms"]), str(after["corridor_rooms"])
rebuilt = [c for c in l2_step + l2_all if c[0] / c[1] >= 0.25]
T["r2_luna_rebuilt"] = words(len(rebuilt))
T["r2_luna_rebuilt_steps"] = words(sum(1 for c in rebuilt if c in l2_step))
assert all(c[5][1] in (1, 2) for c in rebuilt), "every GPT-6 Luna call that removed a quarter of the house or more was in a budget house"
step_redesigns = [c for c in l2_step if c in rewired or c in rebuilt]
assert sorted(c[5][1] for c in step_redesigns) == [1, 2] and len({c[6] for c in step_redesigns}) == 1, \
    "GPT-6 Luna redesigned by a one-room step once in each budget house, at the same step"
T["r2_luna_redesign_step"] = str(step_redesigns[0][6])
assert all(after > before for before, after in map(corridor_change, rewired + rebuilt)), \
    "every GPT-6 Luna call that rewired or rebuilt the house raised corridor rooms"
s2_final = {h: [r2.scores(c, "step", 30)["corridor_rooms"] for c in S2 if c[1] == h] for h in range(1, 5)}
l2_final = {c[1]: r2.scores(c, "step", 30)["corridor_rooms"] for c in L2}
assert all(min(s2_final[h]) > seed_sc[h]["corridor_rooms"] and l2_final[h] > seed_sc[h]["corridor_rooms"] for h in range(1, 5)), \
    "run 2: every chain ended with more corridor rooms than its seed house"
assert all(l2_final[h] > max(s2_final[h]) for h in range(1, 5)), "run 2: GPT-6 Luna ended with more corridor rooms than both Sonnet chains, in every house"
walk = lambda chains, h: [r2.scores(c, "step", 30)["walking_distance"] for c in chains if c[1] == h]
assert all(max(walk(L2, h)) < min(walk(S2, h)) for h in (1, 2)) and all(min(walk(L2, h)) > max(walk(S2, h)) for h in (3, 4)), \
    "run 2: GPT-6 Luna's houses were shorter to walk than Sonnet's in the budget houses, longer in the planned houses"
for tag, chains in (("s", S2), ("l", L2)):          # after step 30 against all at once from step 0, chain by chain
    for name in ("corridor_rooms", "walking_distance"):
        pairs = [(r2.scores(c, "step", 30)[name], r2.scores(c, "all", 0)[name]) for c in chains]
        T["r2_%s_%s_lower" % (tag, name[:4])] = words(sum(a < b for a, b in pairs))
        T["r2_%s_%s_higher" % (tag, name[:4])] = words(sum(a > b for a, b in pairs))
assert all(T["r2_s_%s_%s" % (n, d)] != "no" for n in ("corr", "walk") for d in ("lower", "higher")), \
    "run 2: for Sonnet, neither kind of house came out consistently better on corridor rooms or walking distance"
assert T.pop("r2_l_corr_lower") == "no" and T["r2_l_corr_higher"] == words(len(L2)), "run 2: for GPT-6 Luna, step 30 had more corridor rooms in every chain"
T["r2_s_chains"], T["r2_l_chains"] = words(len(S2)), words(len(L2))
T["r2_s_versions"] = ", ".join(sorted({(r.get("agent_version") or r["claude_code"]).split()[0] for r in r2.records if r["label"].startswith("sonnet55")}))
T["r2_l_version"] = sorted({r["agent_version"].split("\n")[0].rstrip(".") for r in r2.records if r["label"].startswith("gpt6luna")})[0]

# ---- run 3: reorganise first
r3 = Run("runs_100_rooms_refactor")
S3 = [c for c in r3.chains if c[0] == "sonnet55"]
D3 = [c for c in r3.chains if c[0] == "deepseekflash"]
assert sorted(c[1] for c in S3) == [1, 2, 3, 4], "run 3 has one Sonnet chain per seed house"
assert sorted((c[1], c[2]) for c in D3) == [(1, 5), (3, 7)], "run 3 has DeepSeek chains for houses 1 and 3"
missing3 = [(c, (k, s)) for c in S3 + D3 for k, s in [("all", i) for i in range(LAST_ALL + 1)] + [("step", i) for i in range(1, 31)]
            if (k, s) not in r3.calls[c]]
assert len(missing3) == 1 and missing3[0][0] == ("deepseekflash", 1, 5) and missing3[0][1] == ("all", 2), \
    "run 3: one call has no valid house, the all-at-once from step 2 in the DeepSeek house 1 chain"
T["r3_missing"] = "the all-at-once call from step %d in %s" % (missing3[0][1][1], chain_name(missing3[0][0]))
T["r3_final_sonnet"] = final_table(r3, ["sonnet55"])
T["r3_final_deepseek"] = final_table(r3, ["deepseekflash"])
T["r3_changes"] = change_table(r3, ["sonnet55", "deepseekflash"], hallways=True)
T["r3_tries"] = tries_table(r3, ["sonnet55", "deepseekflash"])
T["r3_along"] = along_tables(r3)

pairs3 = [(c, r3.scores(c, "step", 30), r3.scores(c, "all", 0)) for c in S3 + D3]
T["r3_chains"] = words(len(pairs3))
T["r3_corr_lower"] = words(sum(a["corridor_rooms"] < b["corridor_rooms"] for _, a, b in pairs3))
T["r3_corr_same"] = words(sum(a["corridor_rooms"] == b["corridor_rooms"] for _, a, b in pairs3))
T["r3_corr_higher"] = words(sum(a["corridor_rooms"] > b["corridor_rooms"] for _, a, b in pairs3))
T["r3_walk_lower"] = words(sum(a["walking_distance"] < b["walking_distance"] for _, a, b in pairs3))
T["r3_walk_higher"] = words(sum(a["walking_distance"] > b["walking_distance"] for _, a, b in pairs3))
assert (T["r3_corr_lower"], T["r3_corr_same"], T["r3_corr_higher"]) == ("one", "four", "one"), \
    "run 3: step 30 had fewer corridor rooms in one chain, the same in four, more in one"
assert (T["r3_walk_lower"], T["r3_walk_higher"]) == ("five", "one"), \
    "run 3: step 30 was shorter to walk in five chains and longer in one"
T["r3_step30_zero"] = words(sum(r3.scores(c, "step", 30)["corridor_rooms"] == 0 for c in S3 + D3))
T["r3_all00_zero"] = words(sum(r3.scores(c, "all", 0)["corridor_rooms"] == 0 for c in S3 + D3))
assert T["r3_step30_zero"] == "five" and T["r3_all00_zero"] == "five", "run 3: five final houses of each kind have corridor rooms 0"
assert r3.scores(("sonnet55", 1, 1), "step", 30)["corridor_rooms"] == 1, "run 3: the Sonnet house 1 after step 30 has 1 corridor room"
assert [c for c in r3.changes("deepseekflash", "all") if c[5] == ("deepseekflash", 1, 5) and c[6] == 0][0][0] == 1, \
    "run 3: the DeepSeek house 1 all at once from step 0 removed one room"
assert r3.scores(("deepseekflash", 1, 5), "all", 0)["corridor_rooms"] == r3.seed_score(1)["corridor_rooms"], \
    "run 3: the one all-at-once call that did not rebuild kept the seed's corridor rooms"

for tag, model in (("s", "sonnet55"), ("d", "deepseekflash")):
    for kind, _ in KINDS:
        ch = r3.changes(model, kind)
        T["r3_%s_%s_calls" % (tag, kind)] = str(len(ch))
        T["r3_%s_%s_removed" % (tag, kind)] = words(sum(1 for c in ch if c[0]))
        T["r3_%s_%s_max" % (tag, kind)] = str(max(c[0] for c in ch))
        T["r3_%s_%s_kept" % (tag, kind)] = "%.1f%%" % (100 * min(1 - c[0] / c[1] for c in ch))
        T["r3_%s_%s_hall" % (tag, kind)] = "%.2f" % st.mean(c[2] for c in ch)
T["r3_s_first"] = and_list(str(c[0]) for c in r3.changes("sonnet55", "step") if c[6] == 1)
T["r3_d_first"] = and_list(str(c[0]) for c in r3.changes("deepseekflash", "step") if c[6] == 1)
assert int(T["r3_s_first"].split(",")[0]) > 0 and int(T["r3_d_first"].split()[0]) > 0, \
    "run 3: the first one-room steps removed rooms from the seed house"
assert float(T["r3_d_step_kept"].rstrip("%")) < float(T["r3_s_step_kept"].rstrip("%")), \
    "run 3: the DeepSeek one-room steps kept less of the house than the Sonnet ones"
assert min(r3.scores(c, "step", 30)["walking_distance"] for c in D3) > max(r3.scores(c, "step", 30)["walking_distance"] for c in S3), \
    "run 3: the DeepSeek final houses walked further than the Sonnet ones"
T["r3_s_versions"] = ", ".join(sorted({r["claude_code"].split()[0] for r in r3.records if r["label"].startswith("sonnet55")}))
T["r3_adapter_version"] = sorted({r.get("agent_version") for r in r3.records if r["label"].startswith("deepseekflash")})[0]
assert T["r3_adapter_version"] == "1", "run 3: one adapter version"


def script_costs(run, model, kind):
    """The cost of every valid script of this model and kind, at the prices the prompt gives."""
    return [r["cost"] for c in run.chains if c[0] == model for (k, _), r in run.calls[c].items() if k == kind]


def pair_counts(run, chains, tag):
    """After step 30 against all at once from step 0, chain by chain: how many lower, the same and higher."""
    for name in ("corridor_rooms", "walking_distance"):
        pairs = [(run.scores(c, "step", 30)[name], run.scores(c, "all", 0)[name]) for c in chains]
        T["%s_%s_lower" % (tag, name[:4])] = words(sum(a < b for a, b in pairs))
        T["%s_%s_higher" % (tag, name[:4])] = words(sum(a > b for a, b in pairs))


def complete(run, chains):
    return all((k, s) in run.calls[c] for c in chains for k, s in [("all", i) for i in range(LAST_ALL + 1)] + [("step", i) for i in range(1, 31)])


# ---- run 4: reorganise, with cost
r4 = Run("runs_100_rooms_refactor_cost")
S4 = [c for c in r4.chains if c[0] == "sonnet55"]
D4 = [c for c in r4.chains if c[0] == "deepseekflash"]
assert sorted((c[1], c[2]) for c in S4) == [(1, 5), (2, 6), (3, 7), (4, 8)], "run 4 has Sonnet chains 5 to 8, one per seed house"
assert sorted((c[1], c[2]) for c in D4) == [(1, 1), (3, 3)], "run 4 has DeepSeek chains for houses 1 and 3"
assert complete(r4, S4 + D4), "every run 4 chain has all 59 houses"
T["r4_final_sonnet"] = final_table(r4, ["sonnet55"])
T["r4_final_deepseek"] = final_table(r4, ["deepseekflash"])
T["r4_changes"] = change_table(r4, ["sonnet55", "deepseekflash"], hallways=True)
T["r4_tries"] = tries_table(r4, ["sonnet55", "deepseekflash"])
T["r4_along"] = along_tables(r4)
pair_counts(r4, S4, "r4_s")
assert (T["r4_s_corr_lower"], T["r4_s_corr_higher"]) == ("one", "three"), "run 4: Sonnet step 30 had fewer corridor rooms in one house, more in three"
assert (T["r4_s_walk_lower"], T["r4_s_walk_higher"]) == ("three", "one"), "run 4: Sonnet step 30 was shorter to walk in three houses, longer in one"
assert all(r4.scores(c, k, s)["corridor_rooms"] == 0 for c in D4 for k, s in (("step", 30), ("all", 0))), \
    "run 4: the DeepSeek houses after step 30 and all at once from step 0 have corridor rooms 0"
assert all(r4.scores(c, "step", 30)["walking_distance"] > r4.scores(c, "all", 0)["walking_distance"] for c in D4), \
    "run 4: the DeepSeek houses after step 30 were longer to walk than all at once from step 0"
s4_step, s4_all = r4.changes("sonnet55", "step"), r4.changes("sonnet55", "all")
T["r4_s_step_calls"], T["r4_s_all_calls"] = str(len(s4_step)), str(len(s4_all))
T["r4_s_step_removed"], T["r4_s_all_removed"] = words(sum(1 for c in s4_step if c[0])), str(sum(1 for c in s4_all if c[0]))
T["r4_s_most"] = "%.1f%%" % (100 * most_refactored(r4, "sonnet55"))
T["r3_s_most"] = pct(most_refactored(r3, "sonnet55"))
assert most_refactored(r4, "sonnet55") < 0.1, "run 4: no Sonnet call removed 10% or more of the house"
T["r3_d_steps_big"] = and_list(str(n) for n in refactoring(r3, "deepseekflash", "step"))
T["r4_d_steps_big"] = and_list(str(n) for n in refactoring(r4, "deepseekflash", "step"))
T["r4_d_all_big"] = and_list(str(n) for n in refactoring(r4, "deepseekflash", "all"))
assert all(a > b for a, b in zip(refactoring(r3, "deepseekflash", "step"), refactoring(r4, "deepseekflash", "step"))), \
    "run 4: DeepSeek one-room steps removed 10% or more less often than in run 3, house by house"
T["r4_d_first"] = and_list(pct(share(calls[0])) for calls in by_chain(r4, "deepseekflash", "step"))
T["r4_d_most"] = pct(most_refactored(r4, "deepseekflash"))
s4_cost = script_costs(r4, "sonnet55", "step")
T["r4_s_step_cost"], T["r4_s_step_cost_max"] = "%d" % st.median(s4_cost), str(max(s4_cost))
assert st.median(s4_cost) == 5, "run 4: the median Sonnet one-room script cost 5, a room and a door"
T["r4_d_step_cost"], T["r4_d_step_cost_max"] = "%g" % st.median(script_costs(r4, "deepseekflash", "step")), str(max(script_costs(r4, "deepseekflash", "step")))
T["r4_s_versions"] = ", ".join(sorted({r["claude_code"].split()[0] for r in r4.records if r["label"].startswith("sonnet55")}))

# ---- run 5: cost, no reorganise
r5 = Run("runs_100_rooms_cost")
S5 = [c for c in r5.chains if c[0] == "sonnet55"]
D5 = [c for c in r5.chains if c[0] == "deepseekflash"]
assert sorted((c[1], c[2]) for c in S5) == [(1, 5), (3, 7)], "run 5 has Sonnet chains 5 and 7, houses 1 and 3"
assert sorted((c[1], c[2]) for c in D5) == [(1, 1), (3, 3)], "run 5 has DeepSeek chains for houses 1 and 3"
assert complete(r5, S5 + D5), "every run 5 chain has all 59 houses"
T["r5_final_sonnet"] = final_table(r5, ["sonnet55"])
T["r5_final_deepseek"] = final_table(r5, ["deepseekflash"])
T["r5_changes"] = change_table(r5, ["sonnet55", "deepseekflash"], hallways=True)
T["r5_tries"] = tries_table(r5, ["sonnet55", "deepseekflash"])
T["r5_along"] = along_tables(r5)
s5_pairs = [(c, r5.scores(c, "step", 30), r5.scores(c, "all", 0)) for c in S5]
assert all(abs(a["corridor_rooms"] - b["corridor_rooms"]) <= 2 and abs(a["walking_distance"] - b["walking_distance"]) < 0.15
           for _, a, b in s5_pairs), "run 5: for Sonnet, step 30 and all at once from step 0 ended within two corridor rooms and 0.15 of walking distance"
T["r5_s_pairs"] = and_list("%d against %d in house %d" % (a["corridor_rooms"], b["corridor_rooms"], c[1]) for c, a, b in s5_pairs)
d5 = {c[1]: (r5.scores(c, "step", 30)["corridor_rooms"], r5.scores(c, "all", 0)["corridor_rooms"]) for c in D5}
assert d5[1][0] < d5[1][1] and d5[3][0] > d5[3][1], "run 5: DeepSeek step 30 had fewer corridor rooms in house 1, more in house 3"
for tag, model in (("s", "sonnet55"), ("d", "deepseekflash")):
    assert most_refactored(r5, model) < 0.1, "run 5: no call removed 10% or more of the house"
    for kind, _ in KINDS:
        ch = r5.changes(model, kind)
        T["r5_%s_%s_calls" % (tag, kind)] = str(len(ch))
        T["r5_%s_%s_removed" % (tag, kind)] = words(sum(1 for c in ch if c[0]))
        T["r5_%s_%s_hall" % (tag, kind)] = "%.2f" % st.mean(c[2] for c in ch)
assert T.pop("r5_s_step_removed") == "no" and max(c[0] for c in r5.changes("sonnet55", "all")) == 1, \
    "run 5: no Sonnet one-room step removed a room, and no all-at-once call more than one"
assert max(c[0] for kind, _ in KINDS for c in r5.changes("deepseekflash", kind)) == 1, "run 5: no DeepSeek call removed more than one room"
T.pop("r5_d_step_removed"), T.pop("r5_d_all_removed")
for k in ("r5_s_step_calls", "r5_d_step_calls", "r5_d_all_calls", "r5_d_step_hall", "r5_d_all_hall", "r5_s_step_hall"):
    T.pop(k)
s5_cost = script_costs(r5, "sonnet55", "step")
assert set(s5_cost) == {5}, "run 5: every Sonnet one-room script cost 5, a room and a door"
seed_corr = {h: r5.seed_score(h)["corridor_rooms"] for h in (1, 3)}
assert all(r5.scores(c, "all", 0)["corridor_rooms"] > seed_corr[c[1]] for c in S5), \
    "run 5: the Sonnet houses built all at once from step 0 had more corridor rooms than their seed houses"
T["r5_s_all00_corr"] = and_list("from %d to %d in house %d" % (seed_corr[c[1]], r5.scores(c, "all", 0)["corridor_rooms"], c[1]) for c in S5)
r1_all00_s = [r1.scores(c, "all", 0)["corridor_rooms"] - seed_sc[c[1]]["corridor_rooms"] for c in S1]
assert max(r1_all00_s) <= 1, "run 1: all at once from step 0 kept the seed's corridor rooms (within one)"
T["r5_s_versions"] = ", ".join(sorted({r["claude_code"].split()[0] for r in r5.records if r["label"].startswith("sonnet55")}))
T["r145_adapter_version"] = and_list(sorted({r.get("agent_version") for run in (r1, r4, r5) for r in run.records if r["label"].startswith("deepseekflash")}))
assert T["r145_adapter_version"] == T["r3_adapter_version"], "every DeepSeek chain used the same adapter version"
T.pop("r145_adapter_version")

# ---- how long a call takes
def call_hours(model):
    """Per chain, the hours its agent spent on calls (every try); the earliest runs saved no call times and are left out.
    Waiting for a usage limit to reset is not time spent in a call, so a chain that was paused counts like any other."""
    hours = defaultdict(float)
    for run in (r1, r2, r3, r4, r5):
        for r in run.records:
            m = LABEL.match(r["label"])
            if m[1] == model and r.get("call_duration_ms") is not None:
                hours[(run.folder, m[3], m[4])] += r["call_duration_ms"] / 3.6e6
    return list(hours.values())


def call_seconds(model):
    return [r["call_duration_ms"] / 1000 for run in (r1, r2, r3, r4, r5) for r in run.records
            if r["label"].startswith(model) and r.get("call_duration_ms") is not None]


T["call_s_sonnet"], T["call_s_deepseek"] = "%.0f" % st.mean(call_seconds("sonnet55")), "%.0f" % st.mean(call_seconds("deepseekflash"))
T["chain_h_sonnet"], T["chain_h_deepseek"] = "%.1f" % st.mean(call_hours("sonnet55")), "%.1f" % st.mean(call_hours("deepseekflash"))
assert st.mean(call_seconds("deepseekflash")) > 4 * st.mean(call_seconds("sonnet55")), "a DeepSeek call takes many times as long as a Sonnet call"
assert st.mean(call_hours("deepseekflash")) > 4 * st.mean(call_hours("sonnet55")), "a DeepSeek chain takes many times as long as a Sonnet chain"

# ---- the conclusion, as written: check every figure it gives
first = lambda run, model, kind: [share(calls[0]) for calls in by_chain(run, model, kind)]
assert round(100 * most_refactored(r1, "sonnet55")) <= 3 and round(100 * most_refactored(r5, "sonnet55")) <= 3, \
    "conclusion: in runs 1 and 5 no Sonnet call refactored more than 3% of the house"
assert round(100 * most_refactored(r4, "sonnet55"), 1) <= 2.2, "conclusion: in run 4 no Sonnet call refactored more than 2.2% of the house"
s3_first = sorted(round(100 * x) for x in first(r3, "sonnet55", "step"))
assert s3_first == [11, 62, 65, 75], "conclusion: run 3, the first Sonnet step refactored 62-75% in three houses and 11% in the fourth"
assert all(69 <= round(100 * x) <= 71 for x in first(r3, "sonnet55", "all")), "conclusion: run 3, the first Sonnet all-at-once call refactored 69-71%"
assert refactoring(r1, "deepseekflash", "all") == [8, 7], "conclusion: run 1, 8 and 7 of 29 DeepSeek all-at-once calls refactored 10% or more"
assert [round(100 * x) for x in first(r1, "deepseekflash", "all")] == [68, 75], "conclusion: run 1, the first DeepSeek all-at-once call refactored 68% and 75%"
assert refactoring(r3, "deepseekflash", "step") == [23, 25], "conclusion: run 3, 23 and 25 of 30 DeepSeek steps refactored 10% or more"
assert r3.calls[("deepseekflash", 1, 5)][("step", 1)]["command_count"] == 297, "conclusion: run 3, house 1's first DeepSeek step used 297 commands"
assert refactoring(r4, "deepseekflash", "step") == [10, 13], "conclusion: run 4, 10 and 13 of 30 DeepSeek steps refactored 10% or more"

O1 = sorted((c for c in r1.chains if c[0] == "opus55"), key=lambda c: c[1])
O4 = [c for c in r4.chains if c[0] == "opus55"]
O5 = [c for c in r5.chains if c[0] == "opus55"]
assert [(c[1], c[2]) for c in O1] == [(1, 9), (2, 10)] and [(c[1], c[2]) for c in O4] == [(1, 9)] and [(c[1], c[2]) for c in O5] == [(1, 9)], \
    "conclusion: Opus ran run 1 on houses 1 and 2, runs 4 and 5 on house 1"
assert complete(r1, O1) and complete(r4, O4) and complete(r5, O5), "every Opus chain has all 59 houses"


def opus_calls(run, chain):
    """Per kind, the share of the house each call removed, step by step in order: {kind: [share, ...]}."""
    return {kind: [share(c) for c in sorted(run.changes("opus55", kind), key=lambda x: x[6]) if c[5] == chain] for kind in ("step", "all")}


o1 = [opus_calls(r1, c) for c in O1]
assert [round(100 * x["step"][0]) for x in o1] == [65, 77] and [round(100 * x["all"][0]) for x in o1] == [67, 67], \
    "conclusion: run 1, Opus's first step refactored 65% and 77%, its first all-at-once call 67% and 67%"
assert all(v < 0.1 for x in o1 for kind in x for v in x[kind][1:]), "conclusion: run 1, no later Opus call refactored 10% or more"
assert all(r1.scores(c, k, s)["corridor_rooms"] <= 1 for c in O1 for k, s in (("step", 30), ("all", 0), ("all", 15))), \
    "conclusion: run 1, all the Opus final houses have 0 or 1 corridor rooms"
o4 = opus_calls(r4, O4[0])
assert round(100 * o4["step"][0]) == 39 and round(100 * o4["all"][0]) == 36, "conclusion: run 4, Opus's first step refactored 39% and its first all-at-once call 36%"
assert all(v < 0.1 for kind in o4 for v in o4[kind][1:]), "conclusion: run 4, no later Opus call refactored 10% or more"
assert all(r4.scores(O4[0], k, s)["corridor_rooms"] == 0 for k, s in (("step", 30), ("all", 0), ("all", 15))), "conclusion: run 4, all the Opus final houses have 0 corridor rooms"
o5 = opus_calls(r5, O5[0])
assert round(100 * max(v for kind in o5 for v in o5[kind]), 1) == 2.4, "conclusion: run 5, no Opus call refactored more than 2.4%"
corridor5 = lambda c: [r5.scores(c, k, s)["corridor_rooms"] for k, s in (("step", 30), ("all", 0), ("all", 15))]
assert corridor5(O5[0]) == [65, 41, 53], "conclusion: run 5, Opus's incremental house had 65 corridor rooms against 41 and 53"
more_than_both = lambda c: corridor5(c)[0] > max(corridor5(c)[1:])
assert more_than_both(O5[0]) and not more_than_both(S5[0]) and not more_than_both(D5[0]), \
    "conclusion: run 5 house 1, only Opus's incremental house had more corridor rooms than both all-at-once houses"
assert S5[0][1] == D5[0][1] == O5[0][1] == 1, "conclusion: the run 5 chains compared are all on house 1"


def successive(run, model):
    """The share of rooms two successive layouts have in common, step by step: the house a step received and the one it left."""
    out = []
    for c in run.chains:
        if c[0] == model:
            for k in range(1, 31):
                before, after = run.start_keys(c, "step", k), run.keys(c, "step", k)
                out.append(len(before & after) / len(before | after))
    return out


for run in (r3, r4):        # when asked to reorganise, DeepSeek's successive layouts are far more distinct than Sonnet's
    s_, d_ = successive(run, "sonnet55"), successive(run, "deepseekflash")
    assert st.median(d_) < st.median(s_) and sum(x < 0.5 for x in d_) / len(d_) > 10 * sum(x < 0.5 for x in s_) / len(s_) and any(x < 0.5 for x in d_), \
        "conclusion: when asked to reorganise, DeepSeek's successive layouts share fewer rooms than Sonnet's"

for k in ("r1_versions", "r2_s_versions", "r3_s_versions", "r4_s_versions", "r5_s_versions"):
    assert re.fullmatch(r"[0-9., ]+", T[k]), k

if __name__ == "__main__":
    text = (ROOT / "paper" / "REPORT_100_rooms.template.md").read_text()
    unused = set(T) - set(re.findall(r"{{(\w+)}}", text))
    assert not unused, "computed but not in the template: %s" % sorted(unused)
    text = re.sub(r"{{(\w+)}}", lambda m: T[m.group(1)], text)
    for run in (r1, r2, r3, r4, r5):
        run.save_cache()
    assert "{{" not in text, "a placeholder has no value"
    (ROOT / "REPORT_100_rooms.md").write_text(text)
    print("wrote REPORT_100_rooms.md,", len(text.splitlines()), "lines,", len(text.split()), "words")
