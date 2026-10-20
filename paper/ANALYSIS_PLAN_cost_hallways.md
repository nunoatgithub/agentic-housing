# Analysis plan: building and demolishing cost, with hallways (written before the data were collected)

Written 2026-10-20, before the first agent call of this run. Nothing below may be changed after the data are in;
any additional analysis is reported as exploratory.

## Question

In the first run (hallways, nothing cost anything) the patch agents kept their houses good by refactoring: in 24
of 42 patch steps they removed a bathroom or bedroom, put a hallway in its cell and placed the room again elsewhere.
Without hallways, a cost made the patch agents purely local, but there was nothing to refactor towards, so it did not
change the houses. Here building and demolishing cost (a room or hallway 4, a door or a window 1, whether built or
removed) in the world with hallways. Does the cost stop the refactoring, and does patching then end worse than
planning?

## Design

* As in `paper/ANALYSIS_PLAN.md` (the first run: houses on a **5×5 grid** with hallways, the same requests, steps,
  retries and stopping), Claude Sonnet 5.5 at **medium** effort, **6 chains**, run with `--hallways`, data in
  `runs_cost_hallways/`.
* The prompt is `house/prompt_template_hallways.txt`. It differs from the first run's prompt
  (`paper/prompt_5x5_run.txt`) in four places: the cost section gives the prices and says the work is also judged by
  the total cost of the script, instead of saying that building and removing cost nothing; rule 6 says hallways
  "may be added or removed" instead of "are free to add or remove"; the language section lists the room types; and
  `wall`, `remove wall` and the two composite commands are gone (no agent used them in any run).
* The planned agent pays for every room and hallway it builds too; there is no budget and no exchange rate between
  cost and quality.
* This run is compared with the first run (`runs/`). Apart from the cost, the prompts differ only in wording and in
  commands that were never used.

## Expectations (stated beforehand)

1. Patch agents remove far fewer rooms than in the first run.
2. The stepwise-patched houses (H) score worse than the planned houses (I), most of all on corridor rooms.

## Analyses

1. Descriptive: for H, I and J and each score, n, mean ± SD, median and range; the number of hallways in each final
   house.
2. For each score, an exact two-sided permutation test of the difference of means, H against I and J against I
   (8 tests), groups treated as independent. Reported uncorrected, with the Bonferroni threshold 0.05 / 8 = 0.006.
3. Corridor rooms: an exact rank-sum test (H against I, J against I) and the number of houses with a corridor score
   of 3 or more, compared with Fisher's exact test (H against I, J against I).
4. Completion: failed calls per kind of agent, split by cause, and the failure rate of planned builds against patch
   steps (Fisher's exact test).
5. The share of the previous house still in place after each patch step (same cell, same room type), the number of
   rooms removed by each patch script, and what the cells of removed rooms held afterwards; described, not tested.
6. The number of distinct first houses (A) among the six chains.
7. Tokens and cost of the agent calls per kind of agent.
8. Patch behaviour against the first run: the number of patch steps that remove no room, one room, several rooms and
   every room, in each run; described, not tested.
9. Cost: the cost of each valid script, per kind of agent; per chain, the total cost of the stepwise route (A to H),
   of the planned build (I) and of the one-shot route (A and J); described.
10. Against the first run: for each score, an exact two-sided permutation test of the difference of means, this run
    against the first run, for H, I and J (12 tests). Reported uncorrected, with the Bonferroni threshold
    0.05 / 12 = 0.004.

## Repeat

Added 2026-10-20, after the first run of this plan and before the first agent call of its repeat. The same design
is run a second time, unchanged, with data in `runs_cost_hallways_2/`, and analysed in the same way. The two runs are
reported side by side, not pooled.
