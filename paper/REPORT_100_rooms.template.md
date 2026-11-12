# Patching versus planning in houses of 70 to 100 rooms

## Abstract

Does a design patched for one new requirement at a time end worse than a design that takes all the remaining
requirements at once? On a small grid it did, but only when every change had a cost and hallways could be built. We
asked the same question with houses big enough that redesigning is no longer casual: houses of 70 rooms grown to 100,
step by step or all at once, from four seed houses, in five runs: with hallways, without hallways, with a request to
reorganise the house before adding to it, with that request and a cost on every command, and with the cost alone. Claude
Sonnet 5.5 refactored only when asked to reorganise, and not even then once every command had a cost: cost prevailed,
and it acted locally. DeepSeek, asked to reorganise, refactored far more than Sonnet, step by step and all at once, and
cost only constrained it. GPT-6 Luna, in the world without hallways, refactored the badly grown houses without being
asked. Refactoring was not the same as improving. In none of the runs did working step by step or all at once give a
clear advantage in the final design; with cost and no request to reorganise, the conditions in which the small grid
showed one, the houses built step by step ended no worse.

## 1. Question

In the first report (`REPORT.md`), on a 5×5 grid with building and demolishing free, adding rooms one at a time never
ended worse than planning, and the agents showed no built-in preference for local changes. Houses of up to 11 rooms
are easy to redesign, so this report repeats the question on houses of 70 rooms grown to 100 on a 15×15 grid, first
with building and demolishing free. Does adding the rooms one at a time end worse than adding all the remaining rooms
at once to the same house? Does the answer depend on the house the agents start from, one that grew under a tight
budget or one that grew without cost constraints? And when no hallway can be built, do the agents redesign the house,
as they did on the small grid, or does its size keep them from it?

The later runs ask two more things. Asked to reorganise the house before adding to it, do the agents refactor? And on
the small grid, with hallways, adding rooms one at a time did end worse than planning once every command had a cost:
does it here, with the request to reorganise and without it?

## 2. How the runs worked

The full design is in [the study design](docs/study-design.md#the-70-to-100-room-runs); in short:

* **Four seed houses of 70 rooms**, made in code. Houses 1 and 2 grew under a tight budget, the way the agents of the
  priced 5×5 runs added rooms; houses 3 and 4 grew without cost constraints, mostly by the change that gave the best
  scores. They were chosen, out of 24 candidates, as the houses whose outcome depended most on how they were extended.
* **Two kinds of agent in every chain.** One room at a time: steps 1 to 30 each add one room to the house the step
  before left. All at once: from the house left after each of steps 0 to 28, one agent adds all the rooms still
  missing. A chain has 59 calls; every agent is fresh, gets no feedback, and hands in one script.
* **Five runs.** In run 1 hallways can be built. In run 2 no hallway can be built; the hallways the seed houses
  already have can be used or removed. In run 3 hallways can be built and every agent is asked to reorganise the
  existing house before adding to it. Run 4 is run 3 with a cost on every command, as in the priced runs on the small
  grid: building or removing a room costs 4, a door or a window 1, and the agent is told that its work is also judged
  by the total cost of its script. Run 5 is run 1 with the same cost, without the request to reorganise.
* **Agents.** Claude Sonnet 5.5 at medium effort through Claude Code: four chains in run 1, one per seed house
  (Claude Code {{r1_versions}}); eight in run 2, two per seed house ({{r2_s_versions}}); four in run 3
  ({{r3_s_versions}}); four in run 4 ({{r4_s_versions}}); and two in run 5, houses 1 and 3 ({{r5_s_versions}}). GPT-6
  Luna at medium effort: four chains in run 2, one per seed house ({{r2_l_version}}). DeepSeek at low thinking through
  a standalone adapter (version {{r3_adapter_version}}): two chains, houses 1 and 3, in runs 1, 3, 4 and 5. The models
  are reported separately.

The runs are described, not tested. Lower is better for every score. Corridor rooms counts the kitchens, bedrooms and
bathrooms that lie on a best route between two other rooms, a best route being one that crosses as few kitchens,
bedrooms and bathrooms as possible.

## 3. Run 1: hallways can be built

### 3.1 The houses at the end

Sonnet 5.5:

{{r1_final}}

DeepSeek adapter, low thinking:

{{r1_final_deepseek}}

Before the run we expected the house after step 30 to score no worse than the house built all at once from step 0, as on
the small grid. In the Sonnet chains that held for walking distance, which was lower after step 30 in every seed house,
and for compactness in {{r1_compact_better}} of the four. It failed for corridor rooms, which was higher after step 30
in every seed house. The all-at-once agents from step 0 left corridor rooms exactly where the seed house had it in
{{r1_all00_same_corridor}} houses, and one higher in the other. Privacy order was the same in every 100-room house of a
seed house. The DeepSeek houses after step 30 and built all at once from step 0 had corridor rooms 0 in both houses. The
scores of every step are in Appendix A.

### 3.2 What the agents changed

{{r1_changes}}

No Sonnet agent refactored the house. A one-room step removed at most one room, and an all-at-once call kept at least
{{r1_all_kept}} of the house it received. The difference between the two kinds of agent was in what they added: a
one-room step added {{r1_step_hall}} hallways on average, an all-at-once call {{r1_all_hall}}.

DeepSeek refactored, mostly when it saw all the rooms at once. Its one-room steps removed rooms in
{{r1_d_step_removed}} of {{r1_d_step_calls}} calls, but only one step in each house removed 10% or more of the house,
up to {{r1_d_step_most}}. Its all-at-once calls removed 10% or more in {{r1_d_all_big}} of the 29 calls in each house,
among them the first call in each house ({{r1_d_all_first}} of the house). A one-room step added {{r1_d_step_hall}}
hallways on average, an all-at-once call {{r1_d_all_hall}}.

### 3.3 Why it happens

In the Sonnet chains, an all-at-once agent sees every missing room, so it can lay out a hallway that serves them all. It
hung that hallway wing behind the house it received and joined the new rooms to it. Almost none of the new rooms became
a passage, so corridor rooms stayed where the house had it; but the wing lies beyond the old house, so every room in it
is further from everything else, and the walk got longer. A one-room agent sees one room. A hallway for one room is
rarely worth it, so it mostly attached the room to a room already there, and every time that room was a bedroom or
bathroom with nothing else in front of it, a new passage was made. Over 30 steps those passages added up.

DeepSeek did not keep the house it was given. Once in each house a one-room step laid more than half of the house out
again, and some of its all-at-once calls did the same; at the end, neither kind of house had a kitchen, bedroom or
bathroom on a best route between two other rooms.

### 3.4 Failed calls and cost

{{r1_tries}}

Every failed call was tried again with a fresh agent and succeeded within three tries; every chain has all 59 houses.
The Sonnet cost is the Claude Code figure; the DeepSeek cost is computed from DeepSeek's published prices.

## 4. Run 2: no hallway can be built

### 4.1 The houses at the end

Sonnet 5.5:

{{r2_final_sonnet}}

GPT-6 Luna:

{{r2_final_luna}}

One call has no valid house: {{r2_missing}}, whose three tries were all rejected; the chain went on without it. The
scores of every step are in Appendix B.

Across the {{r2_s_chains}} Sonnet chains, the house after step 30 had fewer corridor rooms than the house built all at
once from step 0 in {{r2_s_corr_lower}} chains and more in {{r2_s_corr_higher}}; it was shorter to walk in
{{r2_s_walk_lower}} and longer in {{r2_s_walk_higher}}. Across the {{r2_l_chains}} GPT-6 Luna chains, the house after
step 30 had more corridor rooms in all {{r2_l_corr_higher}}; it was shorter to walk in
{{r2_l_walk_lower}} and longer in {{r2_l_walk_higher}}.

Every chain of both models ended with more corridor rooms than its seed house had, and GPT-6 Luna ended with more than
both Sonnet chains in every seed house. In the two budget houses GPT-6 Luna's houses were shorter to walk than
Sonnet's; in the two planned houses they were longer.

### 4.2 What the agents changed

{{r2_changes}}

Sonnet 5.5 changed almost nothing it was given. No all-at-once call removed a room. Of {{r2_sonnet_steps}} one-room
steps, {{r2_sonnet_removing_steps}} removed one room each, all in the planned houses: {{r2_sonnet_gone_hallways}} a
seed hallway and one a bathroom. No one-room step added more than one door beyond those of its new room.

GPT-6 Luna changed the house in two ways. In {{r2_luna_rewired}} of its {{r2_luna_calls}} calls
({{r2_luna_rewired_all}} of them all at once) it added ten or more doors beyond those of its new rooms, opening up the
house it received, in {{r2_luna_rewired_kept}} of them without removing a room; the biggest was
{{r2_luna_big_where}}, which added {{r2_luna_big_doors}} doors and raised corridor rooms from {{r2_luna_big_before}} to
{{r2_luna_big_after}}. And {{r2_luna_rebuilt}} calls removed a quarter of the house or more, {{r2_luna_rebuilt_steps}}
of them a one-room step, all in the budget houses. In each budget house one one-room step, step
{{r2_luna_redesign_step}}, redesigned the house, and the later steps built on that design. Every call that rewired or
rebuilt the house raised corridor rooms.

### 4.3 Why it happens

Without hallways, a new room can only be reached through a room already there, so every addition risks a passage. An
all-at-once agent no longer has a hallway wing to hang the new rooms on, so it attaches them one after another just as
the one-room agents do, and neither kind of house comes out ahead. Sonnet did that and nothing else: it took the house as
given and attached rooms to it. The budget houses arrived with many passages, kept them, and gained more.

GPT-6 Luna did not take the house as given. It opened extra doors between neighbouring rooms, and in the budget
houses it took apart large parts of the house and laid them out again, moving towards a house in which every room
opens onto the rooms around it. Such a house is short to walk, because there is a direct way almost everywhere; but
the direct way runs through bedrooms and bathrooms instead of hallways, so more of them end up on the route between
other rooms. It did so mostly when it saw all the rooms at once, but a single one-room step was enough to redesign a
budget house, so the order in which the rooms arrived did not decide whether the house was redesigned; the model did.

### 4.4 Failed calls and cost

{{r2_tries}}

Copilot CLI does not report tokens or cost for GPT-6 Luna.

## 5. Run 3: reorganise first

### 5.1 The houses at the end

Sonnet 5.5:

{{r3_final_sonnet}}

DeepSeek adapter, low thinking:

{{r3_final_deepseek}}

One call has no valid house: {{r3_missing}}, whose three tries were all rejected; the chain went on without it. The
scores of every step are in Appendix C.

Before the run we expected the house after step 30 to score no worse than the house built all at once from step 0,
as in the free 5×5 runs. The scores no longer settled it: corridor rooms were the same in {{r3_corr_same}} of the {{r3_chains}} chains,
lower after step 30 in {{r3_corr_lower}} and higher in {{r3_corr_higher}}; walking distance was lower after step 30 in
{{r3_walk_lower}} chains and higher in {{r3_walk_higher}}. The difference that mattered was not in the scores: the
agents now rebuilt the house.

The instruction changed what the agents did. The first one-room steps removed most of the seed house and rebuilt it,
and the final houses after step 30 had corridor rooms 0 in {{r3_step30_zero}} of the six. One all-at-once call from
the seed did not rebuild: the agent kept the seed house and added a wing, and the house kept the seed's corridor
rooms; the other houses built all at once from step 0 had corridor rooms 0 in {{r3_all00_zero}} of the six. Once both
kinds of agent rebuilt, the corridor score no longer separated one room at a time from all at once; the difference
that remained was a walk, not a passage.

### 5.2 What the agents changed

{{r3_changes}}

The Sonnet one-room steps removed rooms in {{r3_s_step_removed}} of {{r3_s_step_calls}} calls, up to {{r3_s_step_max}}
in one, and kept as little as {{r3_s_step_kept}} of the house; the all-at-once calls removed rooms in
{{r3_s_all_removed}} of {{r3_s_all_calls}}, up to {{r3_s_all_max}}, and kept as little as {{r3_s_all_kept}}. The
DeepSeek chains removed more: the one-room steps removed rooms in {{r3_d_step_removed}} of {{r3_d_step_calls}} calls,
up to {{r3_d_step_max}}, and kept as little as {{r3_d_step_kept}}; the all-at-once calls removed rooms in
{{r3_d_all_removed}} of {{r3_d_all_calls}}, up to {{r3_d_all_max}}, and kept as little as {{r3_d_all_kept}}. A
one-room step added {{r3_s_step_hall}} hallways on average in the Sonnet chains and {{r3_d_step_hall}} in the DeepSeek
ones; an all-at-once call added {{r3_s_all_hall}} and {{r3_d_all_hall}}.

### 5.3 Why it happens

The reorganise sentence asked every agent to reduce the complexity of the house before adding to it. The Sonnet
agents did: the first one-room steps removed {{r3_s_first}} rooms in the four chains, and the all-at-once calls
removed rooms too. The DeepSeek adapter at low thinking removed more overall: its first steps removed {{r3_d_first}}
rooms, and across its one-room steps it kept as little as {{r3_d_step_kept}} of the house against the Sonnet
{{r3_s_step_kept}}. The houses that were rebuilt the most were not the shortest to walk: the DeepSeek one-room steps kept less of the
house than the Sonnet ones, and the DeepSeek houses were longer to walk. The all-at-once call from the seed in one
DeepSeek chain kept the seed house and added a wing rather than rebuilding; the one-room step that followed rebuilt
it. The instruction is the lever; where it failed, it failed at the individual call. Redesigning was not the same as
improving.

### 5.4 Failed calls and cost

{{r3_tries}}

The Sonnet cost is the Claude Code figure; the DeepSeek cost is computed from DeepSeek's published prices. Run 3 is
a free world: building and demolishing cost nothing.

## 6. Run 4: reorganise, with cost

### 6.1 The houses at the end

Sonnet 5.5:

{{r4_final_sonnet}}

DeepSeek adapter, low thinking:

{{r4_final_deepseek}}

The scores of every step are in Appendix D.

In the Sonnet chains the house after step 30 had more corridor rooms than the house built all at once from step 0 in
{{r4_s_corr_higher}} of the four houses and fewer in {{r4_s_corr_lower}}; it was shorter to walk in
{{r4_s_walk_lower}} and longer in {{r4_s_walk_higher}}. The DeepSeek houses after step 30 and built all at once from
step 0 had corridor rooms 0 in both houses, and the houses after step 30 were longer to walk.

### 6.2 What the agents changed

{{r4_changes}}

With cost, Sonnet did not refactor, although every agent was asked to reorganise. Its one-room steps removed a room in
{{r4_s_step_removed}} of {{r4_s_step_calls}} calls, its all-at-once calls in {{r4_s_all_removed}} of
{{r4_s_all_calls}}, and no call removed more than {{r4_s_most}} of the house it received; in run 3, without cost, a
single call removed up to {{r3_s_most}}.

DeepSeek still refactored. Its first one-room step removed {{r4_d_first}} of the house, and one call up to
{{r4_d_most}}. Its one-room steps removed 10% or more of the house in {{r4_d_steps_big}} of the 30 steps in each house,
against {{r3_d_steps_big}} in run 3; its all-at-once calls in {{r4_d_all_big}} of 29.

### 6.3 Why it happens

The prompt asks for two things: reorganise the house, and keep the total cost of the script low. Refactoring means
removing rooms and building them again, and every one of those commands has a price. Sonnet chose cost: the median
Sonnet one-room script cost {{r4_s_step_cost}}, the new room and one door, and none cost more than
{{r4_s_step_cost_max}}. It acted locally, as in run 1, where nobody asked it to reorganise. DeepSeek chose to
reorganise: its median one-room script cost {{r4_d_step_cost}}, and one cost {{r4_d_step_cost_max}}. The cost
constrained it, in fewer calls than in run 3, but did not stop it.

### 6.4 Failed calls and cost

{{r4_tries}}

The Sonnet cost is the Claude Code figure; the DeepSeek cost is computed from DeepSeek's published prices.

## 7. Run 5: cost, no reorganise

### 7.1 The houses at the end

Sonnet 5.5:

{{r5_final_sonnet}}

DeepSeek adapter, low thinking:

{{r5_final_deepseek}}

The scores of every step are in Appendix E.

On the small grid, with hallways, cost and no request to reorganise, houses built step by step ended worse than
planned ones. Run 5 has the same conditions at 100 rooms. In the Sonnet chains the house after step 30 and the house
built all at once from step 0 ended with corridor rooms {{r5_s_pairs}}, and with walking distances within 0.15 of
each other. In the DeepSeek chains the house after step 30 had fewer corridor rooms in house 1 and more in house 3.

### 7.2 What the agents changed

{{r5_changes}}

Neither model refactored. No Sonnet one-room step removed a room, and {{r5_s_all_removed}} of its
{{r5_s_all_calls}} all-at-once calls removed one each. No DeepSeek call removed more than one room.

### 7.3 Why it happens

Every Sonnet one-room script cost 5: the new room and one door into a room already there, the cheapest valid answer,
as on the small grid. What differed from the small grid is the all-at-once agent. In run 1, without cost, it hung a
hallway wing behind the house and added {{r1_all_hall}} hallways per call; with cost it added {{r5_s_all_hall}}, and
its houses gained corridor rooms, {{r5_s_all00_corr}}. Both kinds of agent acted locally, so neither kind of house
came out ahead.

### 7.4 Failed calls and cost

{{r5_tries}}

The Sonnet cost is the Claude Code figure; the DeepSeek cost is computed from DeepSeek's published prices.

## 8. Limitations

Each run has one chain per seed house and model, except Sonnet in run 2, which has two. The DeepSeek chains cover
only houses 1 and 3, and so do the Sonnet chains in run 5. Each model ran at one effort level, and GPT-6 Luna in one
run. The DeepSeek chains use a standalone adapter with a clean prompt and low thinking, not Claude Code; they are not
comparable with the Sonnet chains point by point. Claude Code changed version between the runs and within run 2
(Section 2). Single chains show what an agent did, not how often it would do it.

## 9. Conclusion

1. Sonnet 5.5 (medium effort). Its default is to not refactor unless explicitly asked to. But even when asked to, if
additionally instructed to control cost, cost prevails and entails local rather than global change. The only way to
make it act globally is to ask it explicitly to do so and to not mention cost control at the same time. There is no
observed design advantage of using incremental vs all-at-once steps.
- Run 1 (no cost, no reorganise) and run 5 (cost, no reorganise): no call refactored more than 3% of the house.
- Run 3 (no cost, reorganise): the first step refactored 62–75% of the house in three houses and 11% in the fourth.
  The first all-at-once call refactored 69–71%.
- Run 4 (cost, reorganise): no call refactored more than 2.2% of the house.

2. DeepSeek flash (low thinking). There is no clear default about the tendency to act globally when not asked
explicitly to do so. Only that when asked, it refactors far more than Sonnet, step by step and all at once. In that
situation, contrary to Sonnet, cost does not prevent it from refactoring; it only constrains it. There is no clear
advantage of using an incremental or an all-at-once strategy in terms of the final design quality.
- Run 1 (no cost, no reorganise): 1 of 30 steps in each house refactored 10% or more of the house, against 8 and 7
  of 29 all-at-once calls. The first all-at-once call refactored 68% and 75%.
- Run 3 (no cost, reorganise): 23 and 25 of 30 steps refactored 10% or more. In house 1 the first step used 297
  commands to add one bedroom.
- Run 4 (cost, reorganise): 10 and 13 of 30 steps refactored 10% or more.
- Run 5 (cost, no reorganise): no call refactored 10% or more.

3. The 5×5 result. On the 5×5 grid, with hallways, cost and no reorganise, houses built step by step ended worse than
planned ones. Run 5 has the same conditions at 100 rooms, and with Sonnet the two houses showed no difference. There
is no evidence supporting an advantage in working step by step other than the one collected during the 5×5
experiment.

## Appendix A. Run 1, step by step

Each row is one kind of house in one chain: the house after the step, or the house built all at once from the house
after that step. Step 0 of "after the step" is the seed house. All-at-once calls start from steps 0 to 28, so step 30
has none.

{{r1_along}}

## Appendix B. Run 2, step by step

As in Appendix A.

{{r2_along}}

## Appendix C. Run 3, step by step

As in Appendix A.

{{r3_along}}

## Appendix D. Run 4, step by step

As in Appendix A.

{{r4_along}}

## Appendix E. Run 5, step by step

As in Appendix A.

{{r5_along}}

## Reproducibility

The data are in `runs_100_rooms/` (run 1), `runs_100_rooms_no_hallways/` (run 2), `runs_100_rooms_refactor/` (run 3),
`runs_100_rooms_refactor_cost/` (run 4) and `runs_100_rooms_cost/` (run 5); every agent call is one JSON record with its
script, the house it produced, the house's scores and the agent's token usage. The seed houses and the code that made
them are in `runs_100_rooms/seeds/`. The chains were run with `python -m house.run_100_rooms` as described in [running
the experiment](docs/running-the-experiment.md#70-to-100-room-chains); the DeepSeek chains used the standalone adapter.
This report is generated by `python paper/build_report_100_rooms.py` from `paper/REPORT_100_rooms.template.md`.