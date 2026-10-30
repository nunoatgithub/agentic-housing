# Patching versus planning in houses of 70 to 100 rooms

## Abstract

Does a design patched for one new requirement at a time end worse than a design that takes all the remaining
requirements at once? On a small grid, with change free, it did not: the agents patched and planned equally well. We
asked the same question with houses big enough that redesigning is no longer casual: houses of 70 rooms grown to 100,
one room at a time or all the remaining rooms at once, from four seed houses, in a world where hallways can be built
and in one where they cannot. With hallways, the houses grown one room at a time ended with more rooms that must be
walked through, and the houses given all the rooms at once ended longer to walk, because those agents added a hallway
wing behind the house they received. Without hallways, Claude Sonnet 5.5 hardly changed anything it was given, whether
it saw one room or all of them, and neither kind of house came out consistently better. GPT-6 Luna, in the same world,
rewired and rebuilt large parts of the badly grown houses, mostly when it saw all the rooms at once but also in a
single one-room step; its new doors made those houses shorter to walk but put more bedrooms and bathrooms on the way
between rooms. Redesigning was not the same as improving. At this size, whether a house was redesigned
depended on the model more than on how the requirements arrived.

## 1. Question

In the first report (`REPORT.md`), on a 5×5 grid with building and demolishing free, adding rooms one at a time never
ended worse than planning, and the agents showed no built-in preference for local changes. Houses of up to 11 rooms
are easy to redesign, so this report repeats the question on houses of 70 rooms grown to 100 on a 15×15 grid, again
with building and demolishing free. Does adding the rooms one at a time end worse than adding all the remaining rooms
at once to the same house? Does the answer depend on the house the agents start from, one that grew under a tight
budget or one that grew without cost constraints? And when no hallway can be built, do the agents redesign the house,
as they did on the small grid, or does its size keep them from it?

## 2. How the runs worked

The full design is in [the study design](docs/study-design.md#the-70-to-100-room-runs); in short:

* **Four seed houses of 70 rooms**, made in code. Houses 1 and 2 grew under a tight budget, the way the agents of the
  priced 5×5 runs added rooms; houses 3 and 4 grew without cost constraints, mostly by the change that gave the best
  scores. They were chosen, out of 24 candidates, as the houses whose outcome depended most on how they were extended.
* **Two kinds of agent in every chain.** One room at a time: steps 1 to 30 each add one room to the house the step
  before left. All at once: from the house left after each of steps 0 to 28, one agent adds all the rooms still
  missing. A chain has 59 calls; every agent is fresh, gets no feedback, and hands in one script.
* **Two runs.** In run 1 hallways can be built. In run 2 no hallway can be built; the hallways the seed houses already
  have can be used or removed.
* **Agents.** Run 1: four chains of Claude Sonnet 5.5 at medium effort, one per seed house (Claude Code
  {{r1_versions}}). Run 2: eight chains of Sonnet 5.5, two per seed house (Claude Code {{r2_s_versions}}), and four of
  GPT-6 Luna at medium effort, one per seed house ({{r2_l_version}}). The two models are reported separately.

Both runs are described, not tested. Lower is better for every score. Corridor rooms counts the kitchens, bedrooms and
bathrooms that lie on a best route between two other rooms, a best route being one that crosses as few kitchens,
bedrooms and bathrooms as possible.

## 3. Run 1: hallways can be built

### 3.1 The houses at the end

{{r1_final}}

Before the run we expected the house after step 30 to score no worse than the house built all at once from step 0, as
on the small grid. That held for walking distance, which was lower after step 30 in every seed house, and for
compactness in {{r1_compact_better}} of the four. It failed for corridor rooms, which was higher after step 30 in every
seed house. The all-at-once agents from step 0 left corridor rooms exactly where the seed house had it in
{{r1_all00_same_corridor}} houses, and one higher in the other. Privacy order was the same in every 100-room house of
a seed house. The scores of every step are in Appendix A.

### 3.2 What the agents changed

{{r1_changes}}

No agent rebuilt the house. A one-room step removed at most one room, and an all-at-once call kept at least
{{r1_all_kept}} of the house it received. The difference between the two kinds of agent was in what they added: a
one-room step added {{r1_step_hall}} hallways on average, an all-at-once call {{r1_all_hall}}.

### 3.3 Why it happens

An all-at-once agent sees every missing room, so it can lay out a hallway that serves them all. It hung that hallway
wing behind the house it received and joined the new rooms to it. Almost none of the new rooms became a passage, so corridor
rooms stayed where the house had it; but the wing lies beyond the old house, so every room in it is further from
everything else, and the walk got longer. A one-room agent sees one room. A hallway for one room is rarely worth it,
so it mostly attached the room to a room already there, and every time that room was a bedroom or bathroom with
nothing else in front of it, a new passage was made. Over 30 steps those passages added up.

### 3.4 Failed calls and cost

{{r1_tries}}

Every failed call was tried again with a fresh agent and succeeded within three tries; every chain has all 59 houses.

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

## 5. Limitations

Each run has one chain per seed house and model, except Sonnet in run 2, which has two; one effort level; and, for
GPT-6 Luna, one run. Claude Code changed version between the runs and within run 2 (Section 2). Single chains show
what an agent did, not how often it would do it.

## 6. Conclusion

With hallways free, adding rooms one at a time to a big house did end worse than adding them all at once, but only on
one score: the one-room agents created passages, while the all-at-once agents avoided them at the price of a longer
walk. Neither kind of agent redesigned the house.

Without hallways, redesign depended on the model. Sonnet 5.5 kept the house it was given and attached rooms to it,
whether it saw one room or all of them. GPT-6 Luna rewired and rebuilt the badly grown houses, mostly when it saw all
the rooms at once, but also in a single one-room step. Its redesigns made the budget houses shorter to walk and put
more bedrooms and bathrooms on the way between rooms: redesigning was not the same as improving. In neither case did the order in which the rooms arrived decide whether the house got
redesigned.

## Appendix A. Run 1, step by step

Each row is one kind of house in one chain: the house after the step, or the house built all at once from the house
after that step. Step 0 of "after the step" is the seed house. All-at-once calls start from steps 0 to 28, so step 30
has none.

{{r1_along}}

## Appendix B. Run 2, step by step

As in Appendix A.

{{r2_along}}

## Reproducibility

The data are in `runs_100_rooms/` (run 1) and `runs_100_rooms_no_hallways/` (run 2); every agent call is one JSON
record with its script, the house it produced, the house's scores and the agent's token usage. The seed houses and the
code that made them are in `runs_100_rooms/seeds/`. The chains were run with `python -m house.run_100_rooms` as
described in [running the experiment](docs/running-the-experiment.md#70-to-100-room-chains). This report is generated
by `python paper/build_report_100_rooms.py` from `paper/REPORT_100_rooms.template.md`.
