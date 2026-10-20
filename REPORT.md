# Does step-by-step patching degrade design? A controlled test with LLM agents building houses on a grid

**Author:** Nuno Oliveira + Claude Opus 5.5 ·  **Date:** 20 October 2026

---

## Abstract

It is often claimed that an agent asked to make local changes to an existing artefact ends with a worse design than an agent that builds the same final requirements from scratch. We tested this with Claude Sonnet 5.5 in a small world with exact rules: houses built by scripts on a grid, with validity rules and automatic quality scores. A house grows one requested room at a time, each step made by a fresh agent with no memory and no feedback, and is compared with a house planned from scratch for the final requirements and with one patched in a single request. While building and demolishing cost nothing, patching never ended worse than planning: the agents attached rooms while that worked and redesigned when it did not, so they showed no intrinsic bias toward locality. Taking away hallways, or lowering the agents' reasoning effort, did not change this. When every change had a price, step-by-step patching did end worse, in both runs that tested it: the patch agents mostly bought the cheapest attachment rather than the hallway later rooms would need, while agents that saw all the requirements at once built it. Locality came from the price of change, combined with requirements that arrive one at a time.

---

## 1. Introduction

A common claim about AI agents, and about software teams, is that a system grown by a series of local changes ends up worse designed than a system built in one go for the same final requirements, even when nothing stops the person making the change from redesigning. Each change is made where it is most convenient, structure that nobody planned accumulates, and the final shape reflects the order of the requests rather than the requirements.

Software design is hard to measure exactly, so we test the claim in a small world with exact rules: single-floor houses on a grid. A house has rooms that must be reachable, doors, a layout, and familiar design principles (bedrooms are not passages, public rooms sit near the entrance, nothing sticks out). Validity and quality are computed deterministically, without human judgement.

**Hypotheses** (from the project's design document):

* **H1.** The final house produced by patching scores worse than the house planned from scratch for the same requirements.
* **H2.** The gap widens with each change request.

The design compares final houses only, so it tests H1 and cannot test H2.

## 2. Method

### 2.1 The world

A house is a single floor on a **5×5 grid** of 25 cells (rows A–E, columns 1–5). Every room occupies exactly one cell. There are five room types: living room, kitchen, bedroom, bathroom and hallway. Walls are implied: a wall stands on every edge between cells of different rooms, and between a room and the outside or an empty cell. Doors sit in walls and join the rooms on either side; a door in an outer wall leads outside. Windows sit in outer walls.

### 2.2 The language

An agent replies with a script, one command per line:

```
room R6 bedroom C2          place a new room on an empty cell
remove room R6              clear the room and everything on its walls
wall B2|B3                  add a wall (changes nothing: walls already stand)
remove wall B2|B3           rejected if it would join two rooms
door B1|B2                  add a door in the wall between two cells
door A1|north               add a door in an outer wall
remove door B1|B2
window B2|east              add a window in an outer wall
remove window B2|east
add bathroom next to R4     composite: new room in the first free cell next
                            to R4, with a door between them
remove bathroom R5          composite
```

If any line cannot be parsed or carried out, the whole script is rejected and the house is unchanged. Otherwise the house is built, even if it breaks rules.

### 2.3 Validity

A house is valid only if all six rules hold:

1. Every room is reachable from the entrance through doors (the entrance is a living room with a door in an outer wall).
2. Every room shares a wall with another room.
3. Every room has a door to a neighbouring room.
4. Only the living room may have a door in an outer wall.
5. A house has at most one kitchen.
6. The finished house has exactly the requested rooms: for `build:` the listed number of each type; for `add:` the rooms the house already had plus those listed. Hallways are free unless named. Rooms may be removed or rebuilt along the way.

### 2.4 Quality

Four scores, computed for valid houses only, reported separately, lower is better. Rooms are nodes and doors are edges of a graph; *depth* is the number of doors from the entrance room.

| Score | Definition |
|---|---|
| **Corridor rooms** | For each kitchen, bedroom or bathroom *X*, the number of other rooms that cannot be reached from the entrance without passing through *X*; summed over all such *X*. |
| **Privacy order** | Over all pairs of a public room (living room, kitchen) and a private room (bedroom, bathroom): 1 if the private room has smaller depth, ½ if equal, 0 otherwise; the mean over pairs. |
| **Walking distance** | The mean, over all pairs of rooms, of the fewest doors between them. |
| **Compactness** | The number of outer-wall edges minus the smallest possible for that number of cells, 2⌈2√*n*⌉. |

The agents are told the corresponding principles in words (Appendix B), so the scores measure how well an agent met stated principles.

### 2.5 Agents

Claude Sonnet 5.5 (`claude-sonnet-5-5`) at medium reasoning effort, called through Claude Code CLI 2.1.303 in non-interactive mode with tools disabled, no memory, no settings, no saved sessions and an empty working directory. Every call is a fresh conversation that sees only the prompt (Appendix B): the rules, the principles, the statement that building and removing cost nothing, the language, the current layout and a structured request such as `add: bedroom`. The agent gets no feedback of any kind. A step whose script is rejected or whose house is invalid is retried with a fresh agent, up to three tries; if all fail, that chain's patch sequence stops.

### 2.6 Design

Six chains of ten agents each:

| Step | Starts from | Request |
|---|---|---|
| A | empty grid | `build: living room, kitchen, bedroom, bathroom` |
| B, D, F, H | the previous agent's house | `add: bedroom` |
| C, E, G | the previous agent's house | `add: bathroom` |
| **I** (planned) | empty grid | `build: living room, kitchen, bedroom x5, bathroom x4` |
| **J** (one-shot patch) | A's house | `add: bedroom x4, bathroom x3` |

After step H the stepwise-patched house has the same eleven required rooms as I and J, so **H (stepwise patching), I (planning) and J (one-shot patching)** are the three conditions compared. I and J do not depend on steps B to H; when a patch sequence stopped, I and J of that chain were run in a separate pass.

### 2.7 Analysis

The analyses were fixed before the run (`paper/ANALYSIS_PLAN.md`). For each score, an exact two-sided permutation test of the difference of means compares H with I and J with I (eight tests, uncorrected; Bonferroni threshold 0.006). For corridor rooms, an exact rank-sum test and a comparison of the number of houses scoring 3 or more (Fisher's exact test) are added. The groups are treated as independent; Section 3.2 reports how many distinct first houses the chains started from.

## 3. Results

### 3.1 Completion

63 agent calls; 3 failed; 6 of 6 chains produced a valid house at every step (no patch sequence stopped).

| Agent | Calls | Failed | Script rejected: line outside the language | Script rejected: window on a wall that is not outer | Script rejected: other | House invalid: rule 1 | House invalid: rule 6 | House invalid: other rules |
|---|---|---|---|---|---|---|---|---|
| A (first house) | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| B–H (patch steps) | 43 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| I (planned) | 8 | 2 | 0 | 0 | 0 | 2 | 0 | 0 |
| J (patched in one go) | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

The planned build failed in 2 of 8 calls (house broke rule 1: a room could not be reached from the entrance), patch steps in 1 of 43 (a script that placed a room on an occupied cell: "cell B2 is already taken by R4"), and the one-shot patch never failed. Fisher's exact test for planned builds against patch steps gives p = 0.06.

### 3.2 Final houses

Mean ± standard deviation over chains with a valid house at that step.

| House | Chains (n) | Corridor rooms | Privacy order | Walking distance | Compactness |
|---|---|---|---|---|---|
| A (first house) | 6 | 0.00 ± 0.00 | 0.25 ± 0.00 | 1.50 ± 0.00 | 2.00 ± 0.00 |
| H (patched step by step) | 6 | 0.00 ± 0.00 | 0.03 ± 0.00 | 3.09 ± 0.06 | 1.00 ± 1.10 |
| I (planned from scratch) | 6 | 0.00 ± 0.00 | 0.03 ± 0.03 | 3.21 ± 0.19 | 0.33 ± 0.82 |
| J (patched in one go) | 6 | 0.00 ± 0.00 | 0.02 ± 0.01 | 3.12 ± 0.15 | 0.33 ± 0.82 |

| House | Score | Smallest | Median | Largest |
|---|---|---|---|---|
| H (patched step by step) | Corridor rooms | 0.00 | 0.00 | 0.00 |
| H (patched step by step) | Privacy order | 0.03 | 0.03 | 0.03 |
| H (patched step by step) | Walking distance | 3.05 | 3.05 | 3.20 |
| H (patched step by step) | Compactness | 0.00 | 1.00 | 2.00 |
| I (planned from scratch) | Corridor rooms | 0.00 | 0.00 | 0.00 |
| I (planned from scratch) | Privacy order | 0.00 | 0.03 | 0.08 |
| I (planned from scratch) | Walking distance | 3.05 | 3.14 | 3.46 |
| I (planned from scratch) | Compactness | 0.00 | 0.00 | 2.00 |
| J (patched in one go) | Corridor rooms | 0.00 | 0.00 | 0.00 |
| J (patched in one go) | Privacy order | 0.00 | 0.03 | 0.03 |
| J (patched in one go) | Walking distance | 3.05 | 3.05 | 3.42 |
| J (patched in one go) | Compactness | 0.00 | 0.00 | 2.00 |

The six chains started from 3 distinct first houses (the largest group: 3 chains). Distinct final houses: H: 6 of 6, I: 6 of 6, J: 6 of 6.

Corridor rooms was 0 in 18 of 18 final houses, so the principle that bedrooms, bathrooms and the kitchen are never passages was met in every condition. Compactness was 0 in 3 of 6 stepwise-patched houses, 5 of 6 planned houses and 5 of 6 one-shot patched houses. Because the six chains started from 3 distinct first houses, the stepwise and one-shot houses of chains that share a first house are not independent.

### 3.3 Planned tests

| Score | Patched house | n (patched vs planned) | Mean (patched) | Mean (planned I) | Exact permutation p |
|---|---|---|---|---|---|
| Corridor rooms | H step by step | 6 vs 6 | 0.00 | 0.00 | 1.000 (all values equal) |
| Corridor rooms | J in one go | 6 vs 6 | 0.00 | 0.00 | 1.000 (all values equal) |
| Privacy order | H step by step | 6 vs 6 | 0.03 | 0.03 | 1.000 |
| Privacy order | J in one go | 6 vs 6 | 0.02 | 0.03 | 1.000 |
| Walking distance | H step by step | 6 vs 6 | 3.09 | 3.21 | 0.227 |
| Walking distance | J in one go | 6 vs 6 | 3.12 | 3.21 | 0.470 |
| Compactness | H step by step | 6 vs 6 | 1.00 | 0.33 | 0.545 |
| Compactness | J in one go | 6 vs 6 | 0.33 | 0.33 | 1.000 |

| Patched house | Corridor ≥ 3 (patched) | Corridor ≥ 3 (planned I) | Fisher exact p | Rank-sum exact p |
|---|---|---|---|---|
| H step by step | 0 of 6 | 0 of 6 | 1.000 | 1.000 |
| J in one go | 0 of 6 | 0 of 6 | 1.000 | 1.000 |

None of the eight tests comes near the Bonferroni threshold; the smallest p is 0.227 (walking distance, stepwise against planned, where the stepwise-patched houses were slightly shorter to walk). Two of the eight compare columns of equal values and cannot detect anything. The planned comparison of houses with a corridor score of 3 or more is empty: no house in any condition scored above 0.

### 3.4 Along the patch sequence

Mean score of the stepwise-patched house after each step.

| Score | A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|---|
| Corridor rooms | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| Privacy order | 0.25 | 0.08 | 0.06 | 0.05 | 0.04 | 0.04 | 0.03 | 0.03 |
| Walking distance | 1.50 | 1.93 | 2.00 | 2.33 | 2.40 | 2.70 | 2.81 | 3.09 |
| Compactness | 2.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.67 | 0.00 | 1.00 |
| Chains (n) | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |

Free cells before the last patch step: 11.8 (range 11 to 12).

Corridor rooms stayed at 0 after every step. Walking distance rose as rooms were added. Compactness was 0 after steps B to E in every chain and above 0 in some chains after steps F and H.

### 3.5 What the patch agents did

"Unchanged" counts cells holding the same room type before and after a step; it ignores doors.

| Patch steps | Removed no room | Removed 1 room | Removed 2 or more rooms | Median share of the previous layout unchanged | Share of the first house (A) unchanged after step H: smallest / median / largest |
|---|---|---|---|---|---|
| 42 | 18 | 24 | 0 | 0.92 | 0.75 / 0.75 / 0.75 |

In 24 of 42 patch steps the script removed exactly one room (17 bathrooms, 7 bedrooms); afterwards that cell held a hallway in 24 cases, and the removed room had been placed again elsewhere, as rule 6 requires. This breakdown by room type was not in the analysis plan and is descriptive.

### 3.6 Script length and cost

Cost is the harness's list-price estimate. Total 0.87 USD, 0.14 USD per chain. The seven patch calls of a chain used 1.8 times the output tokens of one planned build.

| Agent | Valid scripts | Median commands | Range | Calls | Output tokens per call | of which thinking | Cost (USD, list price) |
|---|---|---|---|---|---|---|---|
| A (build 4 rooms) | 6 | 12 | 11–14 | 6 | 474 | 80% | 0.04 |
| B–H (add one room) | 42 | 10 | 3–13 | 43 | 460 | 87% | 0.51 |
| I (build 11 rooms) | 6 | 44 | 40–46 | 8 | 1,813 | 81% | 0.16 |
| J (add 7 rooms) | 6 | 38 | 34–49 | 6 | 1,954 | 84% | 0.16 |

## 4. Discussion

In this setting we found no sign that patching degraded design. Stepwise-patched, one-shot patched and planned houses met the stated principles to a similar degree, and none of the planned tests found a difference. The patch agents also did not behave like the stereotype of a patcher who attaches each new room wherever it fits: in more than half of the patch steps they moved an existing bedroom or bathroom and put a hallway in its place as part of adding the new room. We did not test whether this behaviour is the reason the corridor score stayed at 0; Section 5 takes the hallways away.

H2 could not be tested, because the planned house was built only for the final requirements.

## 5. A second run: houses without hallways

### 5.1 Why

In the first run every final house had several hallways. A hallway costs nothing and solves any access problem: whatever the patch or the plan, a new room can be reached through one more hallway. Patched and planned houses therefore met the corridor principle in the same way. The assumption behind the second run is that the hallways absorbed whatever difference there was between patching and planning. Without them every cell must hold a requested room, and a house is good or bad only by where its rooms sit and how its doors join them: a patch agent inherits those choices from the earlier steps, a planning agent makes them all at once.

### 5.2 Setup

Everything as in Section 2, with these changes. The language no longer has hallways: the prompt names the four room types and says there are no hallways, rule 6 and the principles no longer mention them, and the example in the layout format is a three-room house instead of a five-room house with a hallway. Windows were kept; nothing measures them. The agents ran through Claude Code CLI 2.1.304, and the analyses were fixed beforehand in `paper/ANALYSIS_PLAN_no_hallways.md`, with the same planned tests as the first run. The houses of the two runs are not compared with each other, because the two worlds differ.

### 5.3 What happened

All six chains produced a valid house at every step.

Without hallways, no final house met the corridor principle: every one, patched or planned, had a corridor score of 3 or more. The hallways were what met it in the first run. Along the patch sequence the score rose with every room added, and the planned houses ended with no fewer forced passages than the stepwise-patched ones. Privacy order was the same in every final house, and none of the eight planned tests came near a difference. Taking the hallways away removed the ceiling of the first run but did not separate patching from planning: what limited the houses was not the order in which the rooms were asked for.

What the patch agents did changed. With hallways, they usually moved one room to make way for a hallway. Without them, they did one of two things: in 32 of 42 patch steps they attached the new room and kept every existing room where it was, and in 7 they removed every room and built the house again. Only three removed a single room. Of the rebuilds, three came at step F, when the house had eight rooms, and two put at least half of the old house back where it was. In two chains the first house was still fully in place after step H; in three at most a quarter of it survived. When attaching got hard, these agents stopped patching and planned again, which supports the reading that at this size the agents are too strong for patching to show its cost: a patch agent that finds attaching hard simply becomes a planner. The three chains whose agents rebuilt ended no better than the three whose agents never rebuilt; this comparison was not in the analysis plan.

## 6. A third run: a weaker agent

### 6.1 Why

In the second run, patch agents that found attaching hard removed every room and built the house again: at this size they were strong enough to turn a patch into a plan. The assumption behind the third run is that a weaker agent rebuilds less often and keeps patching, and that patching then ends worse than planning. The agents stand for coding agents, so the model stays the same and only its reasoning effort is lowered.

### 6.2 Setup

Everything as in the second run (Section 5.2), except that the agents ran at low reasoning effort. The analyses were fixed beforehand in `paper/ANALYSIS_PLAN_no_hallways_low.md`. Since only the effort differs, the patch behaviour of the second and third runs may be compared.

### 6.3 What happened

All six chains produced a valid house at every step, and no patch step failed.

The weaker agents did patch more. In 37 of 42 patch steps they attached the new room and kept every existing room where it was, against 32 at medium effort, and they removed every room in 4 steps, against 7. In three chains the first house was still fully in place after step H.

Patching still did not end worse than planning. The stepwise-patched houses had no more forced passages than the planned ones, privacy order was again the same in every final house, and none of the eight planned tests came near a difference.

How the rooms are joined explains why; this was not in the analysis plan. All but one of the 36 final houses of the second and third runs are trees: every room can be reached from the entrance by exactly one route, so every bedroom, bathroom or kitchen with rooms beyond it is a forced passage. Planning agents built trees just as patch agents did. The one exception, a stepwise-patched house of the third run, has one extra door that closes a loop, and it has the fewest forced passages of all of them. The scores are set by how the agents join the rooms, and planning from scratch did not join them differently. With nothing better to be compared against, patching cannot show a cost, whether the patch agent rebuilds or not.

## 7. Building and demolishing cost

### 7.1 Why

In every run so far nothing cost anything, and the patch agents showed no bias toward locality: they attached rooms while that worked and redesigned, moving a room or rebuilding the whole house, when it did not. If locality does not come from the agent, it may come from what change costs. A first try with a cost, in the world without hallways, made the patch agents purely local (no patch step removed a room) without making patching worse than planning: there was nothing to refactor towards. So the cost is tested here in the world of the first run, with hallways, where the patch agents had kept their houses good by refactoring: in 24 of 42 patch steps they removed a room and put a hallway in its cell.

### 7.2 Setup

Everything as in the first run (Section 2), with hallways, except that building and demolishing cost. The agents are told the prices, and that their work is also judged by the total cost of the script:

```
room, remove room           4 (a room is four walls)
door, remove door           1
window, remove window       1
```

A hallway is a room and costs 4. The planning agent pays for every room and hallway it builds too. There is no budget and no exchange rate between cost and quality, so the trade-off is the agent's own. The prompt (Appendix F) differs from the first run's in three other places: rule 6 says hallways "may be added or removed" instead of "are free to add or remove", the language section lists the room types, and the commands `wall`, `remove wall` and the two composites are gone (no agent used them in any run). The agents were Claude Sonnet 5.5 at medium effort, through Claude Code CLI 2.1.304, in six chains. The analyses were fixed beforehand in `paper/ANALYSIS_PLAN_cost_hallways.md`; the design was then run a second time, unchanged (the repeat), and the two runs are reported side by side. The planned tests are those of the first run, plus a comparison of each score with the first run (12 tests, Bonferroni threshold 0.004).

### 7.3 Results

Agent calls: 62 in the cost run and 64 in the repeat. Every chain produced a valid house at every step in both runs, and no planned build or one-shot patch failed.

| Run | Calls | Failed | Failed patch steps | Failed planned builds | Failed one-shot patches | Causes |
|---|---|---|---|---|---|---|
| Cost run | 62 | 2 | 2 of 44 | 0 of 6 | 0 of 6 | room id already in use (1); house broke rule 6 (1) |
| Repeat | 64 | 4 | 4 of 46 | 0 of 6 | 0 of 6 | line outside the language (3); room id already in use (1) |

Final houses, with the first run for comparison (mean ± standard deviation over six chains):

| Run | House | Corridor rooms | Privacy order | Walking distance | Compactness | Hallways (fewest–most) |
|---|---|---|---|---|---|---|
| First run (no cost) | H (patched step by step) | 0.00 ± 0.00 | 0.03 ± 0.00 | 3.09 ± 0.06 | 1.00 ± 1.10 | 4–5 |
| First run (no cost) | I (planned from scratch) | 0.00 ± 0.00 | 0.03 ± 0.03 | 3.21 ± 0.19 | 0.33 ± 0.82 | 4–7 |
| First run (no cost) | J (patched in one go) | 0.00 ± 0.00 | 0.02 ± 0.01 | 3.12 ± 0.15 | 0.33 ± 0.82 | 4–7 |
| Cost run | H (patched step by step) | 6.83 ± 2.79 | 0.04 ± 0.01 | 2.94 ± 0.12 | 1.67 ± 0.82 | 0–2 |
| Cost run | I (planned from scratch) | 0.00 ± 0.00 | 0.03 ± 0.00 | 3.05 ± 0.00 | 0.00 ± 0.00 | 4–4 |
| Cost run | J (patched in one go) | 0.00 ± 0.00 | 0.03 ± 0.00 | 3.08 ± 0.09 | 0.33 ± 0.82 | 4–5 |
| Repeat | H (patched step by step) | 5.67 ± 2.66 | 0.03 ± 0.01 | 2.86 ± 0.11 | 0.67 ± 1.03 | 0–2 |
| Repeat | I (planned from scratch) | 0.00 ± 0.00 | 0.02 ± 0.01 | 3.12 ± 0.17 | 0.00 ± 0.00 | 4–7 |
| Repeat | J (patched in one go) | 0.00 ± 0.00 | 0.03 ± 0.00 | 3.08 ± 0.09 | 0.33 ± 0.82 | 4–5 |

Planned tests, patched against planned (exact permutation tests; Bonferroni threshold 0.006):

| Score | Patched house | Cost run: mean patched / planned, p | Repeat: mean patched / planned, p |
|---|---|---|---|
| Corridor rooms | H step by step | 6.83 / 0.00, 0.002 | 5.67 / 0.00, 0.002 |
| Corridor rooms | J in one go | 0.00 / 0.00, 1.000 (all equal) | 0.00 / 0.00, 1.000 (all equal) |
| Privacy order | H step by step | 0.04 / 0.03, 0.455 | 0.03 / 0.02, 0.545 |
| Privacy order | J in one go | 0.03 / 0.03, 1.000 (all equal) | 0.03 / 0.02, 1.000 |
| Walking distance | H step by step | 2.94 / 3.05, 0.061 | 2.86 / 3.12, 0.013 |
| Walking distance | J in one go | 3.08 / 3.05, 1.000 | 3.08 / 3.12, 1.000 |
| Compactness | H step by step | 1.67 / 0.00, 0.015 | 0.67 / 0.00, 0.455 |
| Compactness | J in one go | 0.33 / 0.00, 1.000 | 0.33 / 0.00, 1.000 |

| Run | Patched house | Corridor ≥ 3 (patched) | Corridor ≥ 3 (planned I) | Fisher exact p | Rank-sum exact p |
|---|---|---|---|---|---|
| Cost run | H step by step | 6 of 6 | 0 of 6 | 0.002 | 0.002 |
| Cost run | J in one go | 0 of 6 | 0 of 6 | 1.000 | 1.000 |
| Repeat | H step by step | 6 of 6 | 0 of 6 | 0.002 | 0.002 |
| Repeat | J in one go | 0 of 6 | 0 of 6 | 1.000 | 1.000 |

In both runs every stepwise-patched house had a corridor score of 3 or more and no planned house did (p = 0.002 in each run); the houses patched in one go scored 0, like the planned ones. No other planned test passed the threshold.

Against the first run (exact permutation tests; Bonferroni threshold 0.004):

| Score | House | First run (no cost) | Cost run, p against the first run | Repeat, p against the first run |
|---|---|---|---|---|
| Corridor rooms | H | 0.00 | 6.83, 0.002 | 5.67, 0.002 |
| Corridor rooms | I | 0.00 | 0.00, 1.000 | 0.00, 1.000 |
| Corridor rooms | J | 0.00 | 0.00, 1.000 | 0.00, 1.000 |
| Privacy order | H | 0.03 | 0.04, 0.455 | 0.03, 1.000 |
| Privacy order | I | 0.03 | 0.03, 1.000 | 0.02, 1.000 |
| Privacy order | J | 0.02 | 0.03, 1.000 | 0.03, 1.000 |
| Walking distance | H | 3.09 | 2.94, 0.032 | 2.86, 0.011 |
| Walking distance | I | 3.21 | 3.05, 0.182 | 3.12, 0.545 |
| Walking distance | J | 3.12 | 3.08, 0.727 | 3.08, 0.727 |
| Compactness | H | 1.00 | 1.67, 0.545 | 0.67, 1.000 |
| Compactness | I | 0.33 | 0.00, 1.000 | 0.00, 1.000 |
| Compactness | J | 0.33 | 0.33, 1.000 | 0.33, 1.000 |

The cost made the stepwise-patched houses worse than in the first run and left the planned and one-shot houses as they were.

Along the patch sequence (means over chains):

| Run |  | A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|---|---|
| First run (no cost) | corridor rooms | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
|  | hallways | 0.0 | 1.0 | 1.0 | 2.0 | 2.0 | 3.0 | 3.2 | 4.2 |
| Cost run | corridor rooms | 0.00 | 0.33 | 0.83 | 1.83 | 2.83 | 3.83 | 5.50 | 6.83 |
|  | hallways | 0.0 | 0.7 | 0.7 | 0.8 | 0.8 | 0.8 | 0.8 | 0.8 |
| Repeat | corridor rooms | 0.00 | 0.17 | 0.50 | 1.17 | 2.00 | 3.00 | 4.50 | 5.67 |
|  | hallways | 0.0 | 0.8 | 0.8 | 1.2 | 1.2 | 1.2 | 1.2 | 1.2 |

What the patch agents did:

| Run | Patch steps | Removed no room | Removed one room | Removed more | Last step that removed a room | Median cost of a patch script |
|---|---|---|---|---|---|---|
| First run (no cost) | 42 | 18 | 24 | 0 | H | 21.5 |
| Cost run | 42 | 37 | 5 | 0 | D | 5 |
| Repeat | 42 | 35 | 7 | 0 | D | 5 |

Cost of each route at the prices above (mean, smallest–largest):

| Run | Stepwise route A to H | Planned build I | One-shot route A and J | Chains where the stepwise route cost less than I |
|---|---|---|---|---|
| First run, priced the same | 134 (130–138) | 92 (85–100) | 111 (96–141) | 0 of 6 |
| Cost run | 67 (55–83) | 75 (75–75) | 85 (84–89) | 5 of 6 |
| Repeat | 71 (55–83) | 78 (75–90) | 85 (84–89) | 4 of 6 |

The agent calls cost 0.79 USD in the cost run and 0.75 USD in the repeat, at list price. Distinct first houses among the six chains: 3 in the cost run and 2 in the repeat.

### 7.4 Why it happens

Most patch steps cost exactly 5: the new room and one door into a room that was already there. A hallway would cost 4 more, and it pays off only for rooms that have not been requested yet, which the patch agent does not know about. So most steps take the cheapest valid answer and make a bedroom or bathroom a passage. The passages pile up step by step, and the corridor score rises with every patch step. The few refactorings came early: patch steps that removed a room to put a hallway in its cell numbered 5 in the cost run and 7 in the repeat, and none came after step D; in the first run, 24 steps did. No patch step added a hallway after step D. In each run, every stepwise-patched house ended with fewer hallways than every planned house. The planning agent sees all eleven rooms at once and pays for a spine of hallways, and so does the agent that patches in one go: its houses were as good as the planned ones. It is not patching as such that hurts; it is change requested one piece at a time, combined with a cost for each change. In 9 of the 12 chains the stepwise route was also the cheapest of the three routes: the cheapest route gave the worst house.

## 8. Limitations

Each run has six houses per condition from one model (Claude Sonnet 5.5), at medium reasoning effort except in the third run, which used low effort. The six chains started from 3 distinct first houses in the first run, 3 in the second, 3 in the third; in the cost experiment, 3 in the cost run and 2 in the repeat. The comparison of the cost runs with the first run also carries the small prompt differences listed in Section 7.2. Differences smaller than the spread between chains would not be detected.

## 9. Conclusion

On a 5×5 grid, with free redesign and explicit principles, step-by-step patching by Claude Sonnet 5.5 produced houses that scored no worse than houses planned from scratch for the same requirements: every final house met the corridor principle, and no score differed between patching and planning (smallest p = 0.227). The patch agents often moved an existing room to make way for a hallway while adding the new one.

Without hallways, patched and planned houses were equally far from the corridor principle. The patch agents either attached the new room or planned the whole house again: a patch agent that found attaching hard became a planner.

At low effort the agents patched more and rebuilt less, but patching still did not end worse than planning. Planning and patching agents alike joined the rooms as a tree, and that, not the order of the requests, set the scores.

The agents showed no intrinsic bias toward locality. When building and demolishing had a price, in the world with hallways, step-by-step patching did end worse than planning, in both runs: the patch agents mostly bought the cheapest attachment and built no hallway after the first few steps, while agents that saw all the rooms at once, planning or patching in one go, built the hallways. Locality came from the price of change, combined with requirements that arrive one at a time. Other models and higher effort levels were not tested.

## 10. Reproducibility

Code in `house/` as of commit `0f79745`, prompt in `paper/prompt_5x5_run.txt`, analysis plan in `paper/ANALYSIS_PLAN.md`, data (one JSON record per script, raw agent replies) in `runs/`, this report generated by `python paper/build_report.py`. To repeat the run, check out commit `0f79745` and run:

```
python -m house.server --port 8000 --runs runs
python -m house.run_agents --chains 6 --effort medium --runs runs
```

The second run: code in `house/` as of commit `dd9ab04`, prompt in `house/prompt_template.txt` of that commit, analysis plan in `paper/ANALYSIS_PLAN_no_hallways.md`, data in `runs_no_hallways/`. To repeat it, check out commit `dd9ab04` and run:

```
python -m house.server --port 8000 --runs runs_no_hallways
python -m house.run_agents --chains 6 --effort medium --runs runs_no_hallways
```

The third run: the same code as the second run (commit `dd9ab04`), analysis plan in `paper/ANALYSIS_PLAN_no_hallways_low.md`, data in `runs_no_hallways_low/`. To repeat it, check out commit `dd9ab04` and run:

```
python -m house.server --port 8000 --runs runs_no_hallways_low
python -m house.run_agents --chains 6 --effort low --runs runs_no_hallways_low
```

The cost runs: code in `house/` as of commit `25e3cef`, prompt in `house/prompt_template_hallways.txt` of that commit, analysis plan in `paper/ANALYSIS_PLAN_cost_hallways.md`, data in `runs_cost_hallways/` and `runs_cost_hallways_2/`; the first try without hallways (Section 7.1): plan `paper/ANALYSIS_PLAN_cost.md`, data `runs_cost/`. To repeat a cost run, check out commit `25e3cef` and run:

```
python -m house.server --port 8000 --runs runs_cost_hallways
python -m house.run_agents --chains 6 --effort medium --hallways --runs runs_cost_hallways
```

---

## Appendix A. Scores of every final house (first run)

| Chain | House | Corridor rooms | Privacy order | Walking distance | Compactness |
|---|---|---|---|---|---|
| 1 | A | 0 | 0.25 | 1.50 | 2 |
| 1 | H | 0 | 0.03 | 3.05 | 0 |
| 1 | I | 0 | 0.03 | 3.05 | 0 |
| 1 | J | 0 | 0.03 | 3.05 | 0 |
| 2 | A | 0 | 0.25 | 1.50 | 2 |
| 2 | H | 0 | 0.03 | 3.20 | 2 |
| 2 | I | 0 | 0.08 | 3.41 | 0 |
| 2 | J | 0 | 0.03 | 3.12 | 2 |
| 3 | A | 0 | 0.25 | 1.50 | 2 |
| 3 | H | 0 | 0.03 | 3.05 | 0 |
| 3 | I | 0 | 0.03 | 3.05 | 0 |
| 3 | J | 0 | 0.03 | 3.05 | 0 |
| 4 | A | 0 | 0.25 | 1.50 | 2 |
| 4 | H | 0 | 0.03 | 3.12 | 2 |
| 4 | I | 0 | 0.00 | 3.23 | 2 |
| 4 | J | 0 | 0.03 | 3.05 | 0 |
| 5 | A | 0 | 0.25 | 1.50 | 2 |
| 5 | H | 0 | 0.03 | 3.05 | 0 |
| 5 | I | 0 | 0.00 | 3.46 | 0 |
| 5 | J | 0 | 0.03 | 3.05 | 0 |
| 6 | A | 0 | 0.25 | 1.50 | 2 |
| 6 | H | 0 | 0.03 | 3.05 | 2 |
| 6 | I | 0 | 0.03 | 3.05 | 0 |
| 6 | J | 0 | 0.00 | 3.42 | 0 |

## Appendix B. The prompt (first run)

`{{LAYOUT}}` and `{{REQUEST}}` are replaced for each agent; the long layout-format paragraph is wrapped here for printing.

```
You are an experienced, professional house builder. You design single-floor
houses on a 5x5 grid of cells using the house language below. You get one
attempt: reply with a single script containing your whole design. You will
receive no feedback.

RULES (a house that breaks any rule is invalid)
1. Every room is reachable from the entrance through doors.
2. Every room shares a wall with the rest of the house.
3. Every room has at least one door, shared with a neighbouring room.
4. Only the living room may have a door in an outer wall.
5. A house never has more than one kitchen.
6. The finished house has exactly the rooms requested: for "build:" the
   listed number of each room type, for "add:" the rooms already in the
   current layout plus the ones listed. Hallways are free to add or remove
   unless the request names them. You may remove, replace or rebuild rooms
   along the way; only the final count of each requested room type matters.
Anything not forbidden is allowed.

GOOD-HOUSE PRINCIPLES (your work is judged by these)
- Bedrooms, bathrooms and the kitchen are destinations, never passages:
  nobody should have to walk through one to reach another room.
- Public rooms (living room, kitchen) sit near the entrance; private rooms
  (bedrooms, bathrooms) sit further in. Hallways are for passing through.
- Any two rooms should be as few doors apart as possible.
- Keep the house compact, with nothing sticking out.

COST
Building and removing walls, doors, windows and rooms costs nothing.
You may change anything in the current layout.

LANGUAGE
room R6 bedroom C2          place a new room on an empty cell; walls go up around it
remove room R6              clear the room's cells and everything on its walls
wall B2|B3                  add a wall on an edge
remove wall B2|B3           remove a wall between two cells
door B1|B2                  add a door in the wall between two cells
door A1|north               add a door in an outer wall (living room only)
remove door B1|B2
window B2|east              add a window in an outer wall
remove window B2|east
add bathroom next to R4     composite: expands into the commands above
remove bathroom R5          composite

LAYOUT FORMAT
Rows are A to E, columns 1 to 5. Each cell shows the id of the room on it, or
. if empty. Walls are implied: a wall stands on every edge between cells of
different rooms, and on every edge between a room and the outside. Doors and
windows are listed by the edge they sit on.

grid 5x5
     1    2    3    4    5
A    R1   R2   .    .    .
B    R3   R4   .    .    .
C    R5   .    .    .    .
D    .    .    .    .    .
E    .    .    .    .    .

rooms
R1  living room   A1
R2  kitchen       A2
R3  hallway       B1
R4  bedroom       B2
R5  bathroom      C1

doors
A1|north          entrance
A1|A2
A1|B1
B1|B2
B1|C1

windows
A2|north
B2|east

An empty grid has all cells . and empty rooms, doors and windows lists.

CURRENT LAYOUT
{{LAYOUT}}

REQUEST
{{REQUEST}}

Reply with the script only, one command per line.
```

## Appendix C. Example houses (first run, chain 1)

`[ENTRY]` is the entrance, `-[   ]-` a door, `###` a window; a gap on a cell's bottom line in a vertical wall is a door, and an `E` in a vertical wall is an entrance.

```
A (chain 1)                                   H (chain 1)
VALID                                         VALID

      1       2       3       4       5             1       2       3       4       5
  +--###--+[ENTRY]+--###--+                     +--###--+[ENTRY]+--###--+
  |   R2  |   R1  |   R3  |                     |   R2  |   R1  |   R3  |
A |kitchen| living|  bath |                   A |kitchen| living|  bath |
  |                       |                     |                       |
  +-------+-[   ]-+-------+                     +-------+-[   ]-+-------+
          |   R4  |                             |   R6  |   R5  |   R7  |
B         |bedroom|                           B |bedroom|hallway|bedroom|
          #       #                             #                       #
          +--###--+                             +-------+-[   ]-+-------+
                                                |  R11  |   R9  |  R10  |
C                                             C |bedroom|hallway|  bath |
                                                #                       #
                                                +-------+-[   ]-+-------+
                                                |  R14  |  R13  |  R15  |
D                                             D |  bath |hallway|bedroom|
                                                #                       #
                                                +-------+-[   ]-+-------+
                                                |  R18  |  R17  |  R19  |
E                                             E |  bath |hallway|bedroom|
                                                #                       #
                                                +--###--+--###--+--###--+

corridor rooms    0                           corridor rooms    0
privacy order     0.25                        privacy order     0.03
walking distance  1.50                        walking distance  3.05
compactness       2                           compactness       0
```

```
I (chain 1)                                   J (chain 1)
VALID                                         VALID

      1       2       3       4       5             1       2       3       4       5
          +--###--+[ENTRY]+--###--+             +--###--+[ENTRY]+--###--+
          |   R3  |   R1  |   R2  |             |   R2  |   R1  |   R3  |
A         |bedroom| living|kitchen|           A |kitchen| living|  bath |
          |                       |             |                       |
          +-------+-[   ]-+-------+             +-------+-[   ]-+-------+
          |   R8  |   R4  |   R9  |             |   R9  |   R5  |  R10  |
B         |bedroom|hallway|bedroom|           B |  bath |hallway|  bath |
          #                       #             #                       #
          +-------+-[   ]-+-------+             +-------+-[   ]-+-------+
          |  R10  |   R5  |  R11  |             |  R11  |   R6  |  R12  |
C         |bedroom|hallway|bedroom|           C |  bath |hallway|bedroom|
          #                       #             #                       #
          +-------+-[   ]-+-------+             +-------+-[   ]-+-------+
          |  R12  |   R6  |  R13  |             |  R13  |   R7  |  R14  |
D         |  bath |hallway|  bath |           D |bedroom|hallway|bedroom|
          #                       #             #                       #
          +-------+-[   ]-+-------+             +-------+-[   ]-+-------+
          |  R14  |   R7  |  R15  |             |  R15  |   R8  |  R16  |
E         |  bath |hallway|  bath |           E |bedroom|hallway|bedroom|
          #                       #             #                       #
          +-------+-------+-------+             +--###--+-------+--###--+

corridor rooms    0                           corridor rooms    0
privacy order     0.03                        privacy order     0.03
walking distance  3.05                        walking distance  3.05
compactness       0                           compactness       0
```

## Appendix D. Scores of every final house (cost runs)

| Run | Chain | House | Corridor rooms | Privacy order | Walking distance | Compactness | Hallways | Cost of the script |
|---|---|---|---|---|---|---|---|---|
| Cost run | 1 | H | 5 | 0.03 | 2.80 | 2 | 1 | 5 |
| Cost run | 1 | I | 0 | 0.03 | 3.05 | 0 | 4 | 75 |
| Cost run | 1 | J | 0 | 0.03 | 3.05 | 0 | 4 | 64 |
| Cost run | 2 | H | 6 | 0.03 | 2.88 | 2 | 1 | 5 |
| Cost run | 2 | I | 0 | 0.03 | 3.05 | 0 | 4 | 75 |
| Cost run | 2 | J | 0 | 0.03 | 3.05 | 0 | 4 | 64 |
| Cost run | 3 | H | 10 | 0.06 | 3.05 | 2 | 0 | 5 |
| Cost run | 3 | I | 0 | 0.03 | 3.05 | 0 | 4 | 75 |
| Cost run | 3 | J | 0 | 0.03 | 3.26 | 2 | 5 | 69 |
| Cost run | 4 | H | 7 | 0.03 | 3.11 | 2 | 1 | 5 |
| Cost run | 4 | I | 0 | 0.03 | 3.05 | 0 | 4 | 75 |
| Cost run | 4 | J | 0 | 0.03 | 3.05 | 0 | 4 | 64 |
| Cost run | 5 | H | 10 | 0.06 | 2.87 | 2 | 0 | 5 |
| Cost run | 5 | I | 0 | 0.03 | 3.05 | 0 | 4 | 75 |
| Cost run | 5 | J | 0 | 0.03 | 3.05 | 0 | 4 | 64 |
| Cost run | 6 | H | 3 | 0.03 | 2.90 | 0 | 2 | 5 |
| Cost run | 6 | I | 0 | 0.03 | 3.05 | 0 | 4 | 75 |
| Cost run | 6 | J | 0 | 0.03 | 3.05 | 0 | 4 | 64 |
| Repeat | 1 | H | 10 | 0.06 | 2.91 | 0 | 0 | 5 |
| Repeat | 1 | I | 0 | 0.00 | 3.46 | 0 | 7 | 90 |
| Repeat | 1 | J | 0 | 0.03 | 3.05 | 0 | 4 | 64 |
| Repeat | 2 | H | 3 | 0.03 | 2.77 | 0 | 2 | 5 |
| Repeat | 2 | I | 0 | 0.03 | 3.05 | 0 | 4 | 75 |
| Repeat | 2 | J | 0 | 0.03 | 3.05 | 0 | 4 | 64 |
| Repeat | 3 | H | 3 | 0.03 | 2.77 | 0 | 2 | 5 |
| Repeat | 3 | I | 0 | 0.03 | 3.05 | 0 | 4 | 75 |
| Repeat | 3 | J | 0 | 0.03 | 3.05 | 0 | 4 | 64 |
| Repeat | 4 | H | 7 | 0.03 | 3.06 | 2 | 1 | 5 |
| Repeat | 4 | I | 0 | 0.03 | 3.05 | 0 | 4 | 75 |
| Repeat | 4 | J | 0 | 0.03 | 3.26 | 2 | 5 | 69 |
| Repeat | 5 | H | 5 | 0.03 | 2.80 | 2 | 1 | 5 |
| Repeat | 5 | I | 0 | 0.03 | 3.05 | 0 | 4 | 75 |
| Repeat | 5 | J | 0 | 0.03 | 3.05 | 0 | 4 | 64 |
| Repeat | 6 | H | 6 | 0.03 | 2.88 | 0 | 1 | 5 |
| Repeat | 6 | I | 0 | 0.03 | 3.05 | 0 | 4 | 75 |
| Repeat | 6 | J | 0 | 0.03 | 3.05 | 0 | 4 | 64 |

## Appendix E. Example houses (cost run, chain 2)

The stepwise-patched house (H) and the planned house (I) of the chain whose corridor score is nearest the run's median. `[ENTRY]` is the entrance, `-[   ]-` a door; a gap on a cell's bottom line in a vertical wall is a door.

```
H (chain 2)                                   I (chain 2)
VALID                                         VALID

      1       2       3       4       5             1       2       3       4       5
  +-------+[ENTRY]+-------+-------+                     +-------+[ENTRY]+-------+
  |   R2  |   R1  |   R3  |  R13  |                     |   R2  |   R1  |   R3  |
A |kitchen| living|bedroom|bedroom|           A         |kitchen| living|bedroom|
  |                               |                     |                       |
  +-------+-[   ]-+-------+-------+                     +-------+-[   ]-+-------+
  |   R8  |   R5  |   R7  |  R11  |                     |   R8  |   R4  |   R9  |
B |  bath |hallway|bedroom|bedroom|           B         |bedroom|hallway|bedroom|
  |                               |                     |                       |
  +-------+-[   ]-+-------+-------+                     +-------+-[   ]-+-------+
  |  R10  |   R6  |   R9  |                             |  R10  |   R5  |  R11  |
C |  bath |  bath |bedroom|                   C         |bedroom|hallway|bedroom|
  |                       |                             |                       |
  +-------+-------+-[   ]-+                             +-------+-[   ]-+-------+
                  |  R12  |                             |  R12  |   R6  |  R13  |
D                 |  bath |                   D         |  bath |hallway|  bath |
                  |       |                             |                       |
                  +-------+                             +-------+-[   ]-+-------+
                                                        |  R14  |   R7  |  R15  |
E                                             E         |  bath |hallway|  bath |
                                                        |                       |
                                                        +-------+-------+-------+

corridor rooms    6                           corridor rooms    0
privacy order     0.03                        privacy order     0.03
walking distance  2.88                        walking distance  3.05
compactness       2                           compactness       0
```

## Appendix F. The prompt (cost runs)

`{{LAYOUT}}` and `{{REQUEST}}` are replaced for each agent; the long layout-format paragraph is wrapped here for printing.

```
You are an experienced, professional house builder. You design single-floor
houses on a 5x5 grid of cells using the house language below. You get one
attempt: reply with a single script containing your whole design. You will
receive no feedback.

RULES (a house that breaks any rule is invalid)
1. Every room is reachable from the entrance through doors.
2. Every room shares a wall with the rest of the house.
3. Every room has at least one door, shared with a neighbouring room.
4. Only the living room may have a door in an outer wall.
5. A house never has more than one kitchen.
6. The finished house has exactly the rooms requested: for "build:" the
   listed number of each room type, for "add:" the rooms already in the
   current layout plus the ones listed. Hallways may be added or removed
   unless the request names them. You may remove, replace or rebuild rooms
   along the way; only the final count of each requested room type matters.
Anything not forbidden is allowed.

GOOD-HOUSE PRINCIPLES (your work is judged by these)
- Bedrooms, bathrooms and the kitchen are destinations, never passages:
  nobody should have to walk through one to reach another room.
- Public rooms (living room, kitchen) sit near the entrance; private rooms
  (bedrooms, bathrooms) sit further in. Hallways are for passing through.
- Any two rooms should be as few doors apart as possible.
- Keep the house compact, with nothing sticking out.

COST
Every command costs something, whether it builds or removes:
room, remove room           4 (a room is four walls)
door, remove door           1
window, remove window       1
Your work is also judged by the total cost of your script.
You may change anything in the current layout.

LANGUAGE
Room types: living room, kitchen, bedroom, bathroom, hallway.
room R6 bedroom C2          place a new room on an empty cell; walls go up around it
remove room R6              clear the room's cells and everything on its walls
door B1|B2                  add a door in the wall between two cells
door A1|north               add a door in an outer wall (living room only)
remove door B1|B2
window B2|east              add a window in an outer wall
remove window B2|east

LAYOUT FORMAT
Rows are A to E, columns 1 to 5. Each cell shows the id of the room on it, or
. if empty. Walls are implied: a wall stands on every edge between cells of
different rooms, and on every edge between a room and the outside. Doors and
windows are listed by the edge they sit on.

grid 5x5
     1    2    3    4    5
A    R1   R2   .    .    .
B    R3   R4   .    .    .
C    R5   .    .    .    .
D    .    .    .    .    .
E    .    .    .    .    .

rooms
R1  living room   A1
R2  kitchen       A2
R3  hallway       B1
R4  bedroom       B2
R5  bathroom      C1

doors
A1|north          entrance
A1|A2
A1|B1
B1|B2
B1|C1

windows
A2|north
B2|east

An empty grid has all cells . and empty rooms, doors and windows lists.

CURRENT LAYOUT
{{LAYOUT}}

REQUEST
{{REQUEST}}

Reply with the script only, one command per line.
```
