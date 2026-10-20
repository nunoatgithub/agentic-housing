# Analysis plan: houses without hallways (written before the data were collected)

Approved 2026-10-20, before the first agent call. Nothing below may be changed after the data are in;
any additional analysis is reported as exploratory.

## Question

In the 5×5 run every final house had four to seven hallways, and corridor rooms was 0 in all 18 of them. A hallway
costs nothing and fixes any access problem, so patched and planned houses both ended up as rooms hung off a spine of
hallways. Without hallways every cell holds a requested room, and a house is good or bad by where its rooms are and
how its doors join them. Does patching then end worse than planning?

## Design

* As in `paper/ANALYSIS_PLAN.md`, except that the language has no hallways: houses on a **5×5 grid**, the six rules
  and four scores in `HOUSE_DSL.md`; A builds `living room, kitchen, bedroom, bathroom`; B to H each add one room to
  the previous agent's house, alternating bedroom and bathroom; I builds the final 11 rooms from an empty grid; J adds
  all seven rooms to A's house in one request.
* Model: Claude Sonnet 5.5 at **medium** reasoning effort, through `python -m house.run_agents` (fresh agent per
  call, no tools, no memory, no feedback), **6 chains**, data in `runs_no_hallways/`. A failed step is retried with a
  fresh agent, up to 3 tries. If a step still fails, the patch sequence of that chain stops, and steps I and J of that
  chain are run afterwards in a separate pass.
* The prompt is the 5×5 prompt with these changes: the language section starts with "Room types: living room,
  kitchen, bedroom, bathroom. There are no hallways."; rule 6 no longer says that hallways are free to add or remove;
  the principle "Hallways are for passing through." is gone; the example in the layout format is a three-room house
  (living room, kitchen, bedroom) instead of the five-room house with a hallway.
* The houses are not compared with those of the 5×5 run: the two worlds differ.

## Expectation (stated beforehand)

The stepwise-patched houses (H) score worse than the planned houses (I), most of all on corridor rooms.

## Analyses

1. Descriptive: for H, I and J and each score, n, mean ± SD, median and range.
2. For each score, an exact two-sided permutation test of the difference of means, H against I and J against I
   (8 tests), groups treated as independent. Reported uncorrected, with the Bonferroni threshold 0.05 / 8 = 0.006.
3. Corridor rooms: an exact rank-sum test (H against I, J against I) and the number of houses with a corridor score
   of 3 or more, compared with Fisher's exact test (H against I, J against I).
4. Completion: failed calls per kind of agent, split by cause, and the failure rate of planned builds against patch
   steps (Fisher's exact test).
5. The share of the previous house still in place after each patch step (same cell, same room type), the number of
   rooms removed by each patch script, and what the cells of removed rooms held afterwards; described, not tested,
   since the steps of a chain are not independent.
6. The number of distinct first houses (A) among the six chains, since chains that share a first house are not
   independent for H and J.
7. Tokens and cost per kind of agent.
