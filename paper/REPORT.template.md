# Does step-by-step patching degrade design? A controlled test with LLM agents building houses on a grid

**Author:** Nuno  ·  **Date:** 20 October 2026

---

## Abstract

It is often claimed that an agent asked to make local changes to an existing artefact produces a worse design than an agent asked to build the same final requirements from scratch, even when redesign costs nothing. We tested this with Claude Sonnet 5.5 in a small world with exact rules: single-floor houses on a 5×5 grid, six validity rules and four automatic quality scores. In each of six chains, a fresh agent built a four-room house and seven further fresh agents each added one room to the previous agent's house, alternating bedrooms and bathrooms (stepwise patching). For the same final eleven rooms, one fresh agent built the house from scratch (planning) and one added all seven rooms to the first house in a single request (one-shot patching). Agents had no tools, no memory and no feedback, and the analyses were fixed before the run. We found no difference between the three conditions. Corridor rooms was 0 in all {{n_final}} final houses: no room was reachable only through a kitchen, bedroom or bathroom. Privacy order lay between {{privacy_min}} and {{privacy_max}} in every final house, and neither walking distance (on average {{mean_walking_distance_H}} doors stepwise, {{mean_walking_distance_I}} planned, {{mean_walking_distance_J}} one-shot) nor compactness differed between conditions (exact permutation tests, smallest p = {{smallest_p}} among eight). The patch agents did not simply attach rooms: in {{removed_one}} of {{n_patch_steps}} patch steps they removed an existing bathroom or bedroom, put a hallway in its cell and placed the room again elsewhere. {{n_failed}} of {{n_calls}} calls failed.

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

{{n_calls}} agent calls; {{n_failed}} failed; {{complete_chains}} of 6 chains produced a valid house at every step ({{stopped}}).

{{failures}}

The planned build failed in {{planned_fail}} calls ({{planned_fail_reasons}}: a room could not be reached from the entrance), patch steps in {{patch_fail}} (a script that placed a room on an occupied cell: "{{patch_fail_reasons}}"), and the one-shot patch never failed. Fisher's exact test for planned builds against patch steps gives p = {{p_planned_failures}}.

### 3.2 Final houses

Mean ± standard deviation over chains with a valid house at that step.

{{scores}}

{{ranges}}

The six chains started from {{distinct_A}} distinct first houses (the largest group: {{largest_A_group}} chains). Distinct final houses: {{distinct_final}}.

Corridor rooms was 0 in {{corridor_zero_final}} final houses, so the principle that bedrooms, bathrooms and the kitchen are never passages was met in every condition. Compactness was 0 in {{compact_zero_H}} stepwise-patched houses, {{compact_zero_I}} planned houses and {{compact_zero_J}} one-shot patched houses. Because the six chains started from {{distinct_A}} distinct first houses, the stepwise and one-shot houses of chains that share a first house are not independent.

### 3.3 Planned tests

{{tests}}

{{corridor_tests}}

None of the eight tests comes near the Bonferroni threshold; the smallest p is {{smallest_p}} (walking distance, stepwise against planned, where the stepwise-patched houses were slightly shorter to walk). Two of the eight compare columns of equal values and cannot detect anything. The planned comparison of houses with a corridor score of 3 or more is empty: no house in any condition scored above 0.

### 3.4 Along the patch sequence

Mean score of the stepwise-patched house after each step.

{{trajectory}}

Free cells before the last patch step: {{free_before_h}}.

Corridor rooms stayed at 0 after every step. Walking distance rose as rooms were added. Compactness was 0 after steps B to E in every chain and above 0 in some chains after steps F and H.

### 3.5 What the patch agents did

"Unchanged" counts cells holding the same room type before and after a step; it ignores doors.

{{patching}}

In {{removed_one}} of {{n_patch_steps}} patch steps the script removed exactly one room ({{removed_types}}); afterwards that cell held a {{replaced_by}} cases, and the removed room had been placed again elsewhere, as rule 6 requires. This breakdown by room type was not in the analysis plan and is descriptive.

### 3.6 Script length and cost

Cost is the harness's list-price estimate. Total {{cost_total}} USD, {{cost_chain}} USD per chain. The seven patch calls of a chain used {{seq_vs_planned}} times the output tokens of one planned build.

{{cost}}

## 4. Discussion

In this setting we found no sign that patching degraded design. Stepwise-patched, one-shot patched and planned houses met the stated principles to a similar degree, and none of the planned tests found a difference. The patch agents also did not behave like the stereotype of a patcher who attaches each new room wherever it fits: in more than half of the patch steps they moved an existing bedroom or bathroom and put a hallway in its place as part of adding the new room. We did not test whether this behaviour is the reason the corridor score stayed at 0.

H2 could not be tested, because the planned house was built only for the final requirements.

## 5. Limitations

The run has six houses per condition from one model (Claude Sonnet 5.5) at one effort level (medium), and the six chains started from {{distinct_A}} distinct first houses. Differences smaller than the spread between chains would not be detected.

## 6. Conclusion

On a 5×5 grid, with free redesign and explicit principles, step-by-step patching by Claude Sonnet 5.5 produced houses that scored no worse than houses planned from scratch for the same requirements: every final house met the corridor principle, and no score differed between patching and planning (smallest p = {{smallest_p}}). The patch agents often moved an existing room to make way for a hallway while adding the new one. Other models and effort levels were not tested.

## 7. Reproducibility

Code in `house/`, prompt in `house/prompt_template.txt`, analysis plan in `paper/ANALYSIS_PLAN.md`, data (one JSON record per script, raw agent replies) in `runs/`, this report generated by `python paper/build_report.py`. To repeat the run:

```
python -m house.server --port 8000 --runs runs
python -m house.run_agents --chains 6 --effort medium --runs runs
```

---

## Appendix A. Scores of every final house

{{per_chain}}

## Appendix B. The prompt

`{{LAYOUT}}` and `{{REQUEST}}` are replaced for each agent; the long layout-format paragraph is wrapped here for printing.

```
{{prompt}}
```

## Appendix C. Example houses (chain {{example_chain}})

`[ENTRY]` is the entrance, `-[   ]-` a door, `###` a window; a gap on a cell's bottom line in a vertical wall is a door, and an `E` in a vertical wall is an entrance.

```
{{drawing_1}}
```

```
{{drawing_2}}
```
