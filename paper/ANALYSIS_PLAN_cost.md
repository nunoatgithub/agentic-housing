# Analysis plan: building and demolishing cost (written before the data were collected)

Written 2026-10-20, before the first agent call of this run. Nothing below may be changed after the data are in;
any additional analysis is reported as exploratory.

## Question

In the runs without hallways nothing cost anything, and the patch agents attached rooms while that worked and
rebuilt the whole house when it did not: they showed no bias toward locality when redesign is free. Here every
command has a price, whether it builds or removes: a room costs 4, a door or a window 1, and the agents are told
that their work is also judged by the total cost of the script. Does a cost make the patch agents keep to local
changes, and does patching then end worse than planning?

## Design

* As in `paper/ANALYSIS_PLAN_no_hallways.md` (same world without hallways, requests, steps, retries and stopping),
  Claude Sonnet 5.5 at **medium** effort, **6 chains**, data in `runs_cost/`.
* The prompt differs from the second run's in two places: the cost section gives the prices and says the work is
  also judged by the total cost of the script, instead of saying that building and removing cost nothing; and the
  language no longer lists `wall`, `remove wall` and the two composite commands, which no agent used in any run.
* The planned agent pays for every room it builds too; there is no budget and no exchange rate between cost and
  quality.
* Since the prompts differ only in the cost (the dropped commands were never used), this run may be compared with
  the second run in `runs_no_hallways/`.

## Expectations (stated beforehand)

1. Patch agents remove fewer rooms than in the second run: more steps only attach, fewer rebuild the house.
2. The stepwise-patched houses (H) score worse than the planned houses (I).

## Analyses

1. to 7. As in `paper/ANALYSIS_PLAN_no_hallways.md`, on this run.
8. Patch behaviour against the second run: the number of patch steps that remove no room, one room, several rooms
   and every room, in each run; described, not tested, since the steps of a chain are not independent.
9. Cost: the cost of each valid script, per kind of agent; per chain, the total cost of the stepwise route (A to H),
   of the planned build (I) and of the one-shot route (A and J); described.
10. Against the second run: for each score, an exact two-sided permutation test of the difference of means, this
    run against the second run, for H, I and J (12 tests). Reported uncorrected, with the Bonferroni threshold
    0.05 / 12 = 0.004.
