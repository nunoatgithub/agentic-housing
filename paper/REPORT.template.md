# Does step-by-step patching degrade design? A controlled test with LLM agents building houses on a grid

**Author:** Nuno Oliveira + Claude Opus 5.5 ·  **Date:** 20 October 2026

---

## Abstract

It is often claimed that an agent asked to make local changes to an existing artefact produces a worse design than an agent asked to build the same final requirements from scratch, even when redesign costs nothing. We tested this with Claude Sonnet 5.5 in a small world with exact rules: single-floor houses on a 5×5 grid, six validity rules and four automatic quality scores. In each of six chains, a fresh agent built a four-room house and seven further fresh agents each added one room to the previous agent's house, alternating bedrooms and bathrooms (stepwise patching). For the same final eleven rooms, one fresh agent built the house from scratch (planning) and one added all seven rooms to the first house in a single request (one-shot patching). Agents had no tools, no memory and no feedback, and the analyses were fixed before the run. We found no difference between the three conditions. Corridor rooms was 0 in all {{n_final}} final houses: no room was reachable only through a kitchen, bedroom or bathroom. Privacy order lay between {{privacy_min}} and {{privacy_max}} in every final house, and neither walking distance (on average {{mean_walking_distance_H}} doors stepwise, {{mean_walking_distance_I}} planned, {{mean_walking_distance_J}} one-shot) nor compactness differed between conditions (exact permutation tests, smallest p = {{smallest_p}} among eight). The patch agents did not simply attach rooms: in {{removed_one}} of {{n_patch_steps}} patch steps they removed an existing bathroom or bedroom, put a hallway in its cell and placed the room again elsewhere. {{n_failed}} of {{n_calls}} calls failed. A second run without hallways, where every cell must hold a requested room, again found no difference between patching and planning: no final house met the corridor principle, and the patch agents either attached the new room or removed every room and built the house again. A third run, the same model at low effort, patched more and rebuilt less, with the same result: in both runs without hallways almost every house, patched or planned, joined its rooms as a tree, with a single route to each room, and that set its scores. Finally, when building and demolishing had a price, in the world with hallways, step-by-step patching did end worse: in two runs every stepwise-patched house had rooms reachable only through a kitchen, bedroom or bathroom, while every planned house and every house patched in one go had none (exact permutation tests, p = {{ch_p_corridor}}). The patch agents mostly paid for the cheapest attachment, not for a hallway whose benefit would come only with later requests.

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

What the patch agents did changed. With hallways, they usually moved one room to make way for a hallway. Without them, they did one of two things: in {{nh_attached}} of {{nh_patch_steps}} patch steps they attached the new room and kept every existing room where it was, and in {{nh_rebuilt}} they removed every room and built the house again. Only {{nh_one_room}} removed a single room. Of the rebuilds, {{nh_rebuild_step_n}} came at step {{nh_rebuild_step}}, when the house had {{nh_rebuild_step_rooms}} rooms, and {{nh_rebuilt_same}} put at least half of the old house back where it was. In {{nh_a_intact}} chains the first house was still fully in place after step H; in {{nh_a_quarter}} at most a quarter of it survived. When attaching got hard, these agents stopped patching and planned again, which supports the reading that at this size the agents are too strong for patching to show its cost: a patch agent that finds attaching hard simply becomes a planner. The {{nh_rebuild_chains}} chains whose agents rebuilt ended no better than the {{nh_attach_chains}} whose agents never rebuilt; this comparison was not in the analysis plan.

## 6. A third run: a weaker agent

### 6.1 Why

In the second run, patch agents that found attaching hard removed every room and built the house again: at this size they were strong enough to turn a patch into a plan. The assumption behind the third run is that a weaker agent rebuilds less often and keeps patching, and that patching then ends worse than planning. The agents stand for coding agents, so the model stays the same and only its reasoning effort is lowered.

### 6.2 Setup

Everything as in the second run (Section 5.2), except that the agents ran at low reasoning effort. The analyses were fixed beforehand in `paper/ANALYSIS_PLAN_no_hallways_low.md`. Since only the effort differs, the patch behaviour of the second and third runs may be compared.

### 6.3 What happened

All six chains produced a valid house at every step, and no patch step failed.

The weaker agents did patch more. In {{lo_attached}} of {{nh_patch_steps}} patch steps they attached the new room and kept every existing room where it was, against {{nh_attached}} at medium effort, and they removed every room in {{lo_rebuilt}} steps, against {{nh_rebuilt}}. In {{lo_a_intact}} chains the first house was still fully in place after step H.

Patching still did not end worse than planning. The stepwise-patched houses had no more forced passages than the planned ones, privacy order was again the same in every final house, and none of the eight planned tests came near a difference.

How the rooms are joined explains why; this was not in the analysis plan. All but one of the {{nh_lo_final}} final houses of the second and third runs are trees: every room can be reached from the entrance by exactly one route, so every bedroom, bathroom or kitchen with rooms beyond it is a forced passage. Planning agents built trees just as patch agents did. The one exception, a stepwise-patched house of the third run, has one extra door that closes a loop, and it has the fewest forced passages of all of them. The scores are set by how the agents join the rooms, and planning from scratch did not join them differently. With nothing better to be compared against, patching cannot show a cost, whether the patch agent rebuilds or not.

## 7. Building and demolishing cost

### 7.1 Why

In every run so far nothing cost anything, and the patch agents showed no bias toward locality: they attached rooms while that worked and redesigned, moving a room or rebuilding the whole house, when it did not. If locality does not come from the agent, it may come from what change costs. A first try with a cost, in the world without hallways, made the patch agents purely local (no patch step removed a room) without making patching worse than planning: there was nothing to refactor towards. So the cost is tested here in the world of the first run, with hallways, where the patch agents had kept their houses good by refactoring: in {{ch_removed_first}} of 42 patch steps they removed a room and put a hallway in its cell.

### 7.2 Setup

Everything as in the first run (Section 2), with hallways, except that building and demolishing cost. The agents are told the prices, and that their work is also judged by the total cost of the script:

```
room, remove room           4 (a room is four walls)
door, remove door           1
window, remove window       1
```

A hallway is a room and costs 4. The planning agent pays for every room and hallway it builds too. There is no budget and no exchange rate between cost and quality, so the trade-off is the agent's own. The prompt (Appendix F) differs from the first run's in three other places: rule 6 says hallways "may be added or removed" instead of "are free to add or remove", the language section lists the room types, and the commands `wall`, `remove wall` and the two composites are gone (no agent used them in any run). The agents were Claude Sonnet 5.5 at medium effort, through Claude Code CLI 2.1.304, in six chains. The analyses were fixed beforehand in `paper/ANALYSIS_PLAN_cost_hallways.md`; the design was then run a second time, unchanged (the repeat), and the two runs are reported side by side. The planned tests are those of the first run, plus a comparison of each score with the first run (12 tests, Bonferroni threshold 0.004).

### 7.3 Results

Agent calls: {{ch_calls}}. Every chain produced a valid house at every step in both runs, and no planned build or one-shot patch failed.

{{ch_completion}}

Final houses, with the first run for comparison (mean ± standard deviation over six chains):

{{ch_scores}}

Planned tests, patched against planned (exact permutation tests; Bonferroni threshold 0.006):

{{ch_tests}}

{{ch_corridor_tests}}

In both runs every stepwise-patched house had a corridor score of 3 or more and no planned house did (p = {{ch_p_corridor}}); the houses patched in one go scored 0, like the planned ones. No other planned test passed the threshold.

Against the first run (exact permutation tests; Bonferroni threshold 0.004):

{{ch_vs_first}}

The cost made the stepwise-patched houses worse than in the first run and left the planned and one-shot houses as they were.

Along the patch sequence (means over chains):

{{ch_trajectory}}

What the patch agents did:

{{ch_patching}}

Cost of each route at the prices above (mean, smallest–largest):

{{ch_routes}}

The agent calls cost {{ch_money}}, at list price. Distinct first houses among the six chains: {{ch_distinct_A}}.

### 7.4 Why it happens

Most patch steps cost exactly 5: the new room and one door into a room that was already there. A hallway would cost 4 more, and it pays off only for rooms that have not been requested yet, which the patch agent does not know about. So most steps take the cheapest valid answer and make a bedroom or bathroom a passage. The passages pile up step by step, and the corridor score rises with every patch step. The few refactorings came early: patch steps that removed a room to put a hallway in its cell numbered {{ch_removed}}, and none came after step {{ch_last_removal}}; in the first run, {{ch_removed_first}} steps did. No patch step added a hallway after step {{ch_last_hallway}}. In each run, every stepwise-patched house ended with fewer hallways than every planned house. The planning agent sees all eleven rooms at once and pays for a spine of hallways, and so does the agent that patches in one go: its houses were as good as the planned ones. It is not patching as such that hurts; it is change requested one piece at a time, combined with a cost for each change. In {{ch_cheaper}} of the 12 chains the stepwise route was also the cheapest of the three routes: the cheapest route gave the worst house.

## 8. Limitations

Each run has six houses per condition from one model (Claude Sonnet 5.5), at medium reasoning effort except in the third run, which used low effort. The six chains started from {{distinct_A}} distinct first houses in the first run, {{nh_distinct_A}} in the second, {{lo_distinct_A}} in the third; in the cost experiment, {{ch_distinct_A}}. The comparison of the cost runs with the first run also carries the small prompt differences listed in Section 7.2. Differences smaller than the spread between chains would not be detected.

## 9. Conclusion

On a 5×5 grid, with free redesign and explicit principles, step-by-step patching by Claude Sonnet 5.5 produced houses that scored no worse than houses planned from scratch for the same requirements: every final house met the corridor principle, and no score differed between patching and planning (smallest p = {{smallest_p}}). The patch agents often moved an existing room to make way for a hallway while adding the new one.

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

The cost runs: code in `house/` as it is now, prompt in `house/prompt_template_hallways.txt`, analysis plan in `paper/ANALYSIS_PLAN_cost_hallways.md`, data in `runs_cost_hallways/` and `runs_cost_hallways_2/`; the first try without hallways (Section 7.1): plan `paper/ANALYSIS_PLAN_cost.md`, data `runs_cost/`. To repeat a cost run:

```
python -m house.server --port 8000 --runs runs_cost_hallways
python -m house.run_agents --chains 6 --effort medium --hallways --runs runs_cost_hallways
```

---

## Appendix A. Scores of every final house (first run)

{{per_chain}}

## Appendix B. The prompt (first run)

`{{LAYOUT}}` and `{{REQUEST}}` are replaced for each agent; the long layout-format paragraph is wrapped here for printing.

```
{{prompt}}
```

## Appendix C. Example houses (first run, chain {{example_chain}})

`[ENTRY]` is the entrance, `-[   ]-` a door, `###` a window; a gap on a cell's bottom line in a vertical wall is a door, and an `E` in a vertical wall is an entrance.

```
{{drawing_1}}
```

```
{{drawing_2}}
```

## Appendix D. Scores of every final house (cost runs)

{{ch_per_chain}}

## Appendix E. Example houses (cost run, chain {{ch_example_chain}})

The stepwise-patched house (H) and the planned house (I) of the chain whose corridor score is nearest the run's median. `[ENTRY]` is the entrance, `-[   ]-` a door; a gap on a cell's bottom line in a vertical wall is a door.

```
{{ch_drawing}}
```

## Appendix F. The prompt (cost runs)

`{{LAYOUT}}` and `{{REQUEST}}` are replaced for each agent; the long layout-format paragraph is wrapped here for printing.

```
{{ch_prompt}}
```
