# Analysis plan (written before the data were collected)

Written 2026-10-20, before the first agent call of this run. Nothing below may be changed after the data are in;
any additional analysis is reported as exploratory.

## Design

* World: houses on a **5×5 grid** (25 cells), the six hard rules and four scores in `HOUSE_DSL.md`.
* Model: Claude Sonnet 5.5 at **medium** reasoning effort, run through `python -m house.run_agents`
  (fresh agent per call, no tools, no memory, no feedback).
* **6 chains**, each with ten agents: A builds `living room, kitchen, bedroom, bathroom`; B to H each add one room
  to the previous agent's house, alternating bedroom, bathroom, bedroom, bathroom, bedroom, bathroom, bedroom;
  I builds the final 11 required rooms from an empty grid; J adds all seven rooms to A's house in one request.
* A failed step (script rejected or house invalid) is retried with a fresh agent, up to 3 tries. If a step still
  fails, the patch sequence of that chain stops, and steps I and J of that chain are run afterwards in a separate pass.
* The three conditions compared are the final houses of H (stepwise patching), I (planning) and J (one-shot patching).

## Analyses

1. Descriptive: for each condition and score, n, mean ± SD, median and range; the number of rooms and hallways.
2. For each score, an exact two-sided permutation test of the difference of means, H against I and J against I
   (8 tests), groups treated as independent. Reported uncorrected, with the Bonferroni threshold 0.05 / 8 = 0.006.
3. Corridor rooms: an exact rank-sum test (H against I, J against I) and the number of houses with a corridor score
   of 3 or more, compared with Fisher's exact test (H against I, J against I).
4. Completion: failed calls per kind of agent, and the failure rate of planned builds against patch steps
   (Fisher's exact test).
5. The share of the previous house still in place after each patch step (same cell, same room type) and the
   number of rooms removed by each patch script.
6. The number of distinct first houses (A) among the six chains, since chains that share a first house are not
   independent for H and J.
7. Tokens and cost per kind of agent.
