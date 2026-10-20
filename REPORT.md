# Does step-by-step patching degrade design? A controlled test with LLM agents building houses on a grid

**Author:** Nuno Oliveira + Claude Opus 5.5 ·  **Date:** 20 October 2026

---

## Abstract

It is often claimed that an agent asked to make local changes to an existing artefact produces a worse design than an agent asked to build the same final requirements from scratch, even when redesign costs nothing. We tested this with Claude Sonnet 5.5 in a small world with exact rules: single-floor houses on a 5×5 grid, six validity rules and four automatic quality scores. In each of six chains, a fresh agent built a four-room house and seven further fresh agents each added one room to the previous agent's house, alternating bedrooms and bathrooms (stepwise patching). For the same final eleven rooms, one fresh agent built the house from scratch (planning) and one added all seven rooms to the first house in a single request (one-shot patching). Agents had no tools, no memory and no feedback, and the analyses were fixed before the run. We found no difference between the three conditions. Corridor rooms was 0 in all 18 final houses: no room was reachable only through a kitchen, bedroom or bathroom. Privacy order lay between 0.00 and 0.08 in every final house, and neither walking distance (on average 3.09 doors stepwise, 3.21 planned, 3.12 one-shot) nor compactness differed between conditions (exact permutation tests, smallest p = 0.227 among eight). The patch agents did not simply attach rooms: in 24 of 42 patch steps they removed an existing bathroom or bedroom, put a hallway in its cell and placed the room again elsewhere. 3 of 63 calls failed.

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

In this setting we found no sign that patching degraded design. Stepwise-patched, one-shot patched and planned houses met the stated principles to a similar degree, and none of the planned tests found a difference. The patch agents also did not behave like the stereotype of a patcher who attaches each new room wherever it fits: in more than half of the patch steps they moved an existing bedroom or bathroom and put a hallway in its place as part of adding the new room. We did not test whether this behaviour is the reason the corridor score stayed at 0.

H2 could not be tested, because the planned house was built only for the final requirements.

## 5. Limitations

The run has six houses per condition from one model (Claude Sonnet 5.5) at one effort level (medium), and the six chains started from 3 distinct first houses. Differences smaller than the spread between chains would not be detected.

## 6. Conclusion

On a 5×5 grid, with free redesign and explicit principles, step-by-step patching by Claude Sonnet 5.5 produced houses that scored no worse than houses planned from scratch for the same requirements: every final house met the corridor principle, and no score differed between patching and planning (smallest p = 0.227). The patch agents often moved an existing room to make way for a hallway while adding the new one. Other models and effort levels were not tested.

## 7. Reproducibility

Code in `house/`, prompt in `house/prompt_template.txt`, analysis plan in `paper/ANALYSIS_PLAN.md`, data (one JSON record per script, raw agent replies) in `runs/`, this report generated by `python paper/build_report.py`. To repeat the run:

```
python -m house.server --port 8000 --runs runs
python -m house.run_agents --chains 6 --effort medium --runs runs
```

---

## Appendix A. Scores of every final house

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

## Appendix B. The prompt

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

## Appendix C. Example houses (chain 1)

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
