# Analysis plan: houses without hallways, low effort (written before the data were collected)

Written 2026-10-20, before the first agent call of this run. Nothing below may be changed after the data are in;
any additional analysis is reported as exploratory.

## Question

In the run without hallways at medium effort, patch agents that found attaching hard removed every room and built
the house again: at that size they were strong enough to turn a patch into a plan. Does a weaker agent, the same
model at low effort, keep patching, and does patching then end worse than planning?

## Design

* Everything as in `paper/ANALYSIS_PLAN_no_hallways.md` (same world, prompt, requests, steps, retries and stopping),
  except the reasoning effort: Claude Sonnet 5.5 at **low** effort, **6 chains**, data in `runs_no_hallways_low/`.
* Since only the effort differs, this run may be compared with the medium-effort run in `runs_no_hallways/`.

## Expectations (stated beforehand)

1. The stepwise-patched houses (H) score worse than the planned houses (I), most of all on corridor rooms.
2. Patch agents remove every room and rebuild less often than at medium effort.

## Analyses

1. to 7. As in `paper/ANALYSIS_PLAN_no_hallways.md`, on this run.
8. Patch behaviour against the medium-effort run: the number of patch steps that remove no room, one room and every
   room, in each run; described, not tested, since the steps of a chain are not independent.
