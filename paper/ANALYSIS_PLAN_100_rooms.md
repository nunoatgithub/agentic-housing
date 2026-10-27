# Analysis plan: houses of 70 to 100 rooms (written before the data were collected)

Written 2026-10-25, before the first agent call of this run. Nothing below may be changed after the data are in;
any additional analysis is reported as exploratory.

## Question

In the paper's runs where building and demolishing were free, on a 5×5 grid with houses of up to 11 rooms, adding
rooms one at a time never ended worse than planning, and the agents showed no built-in preference for local
changes. This run asks the same question with houses big enough that redesigning is no longer casual: houses of 70
rooms grown to 100 on a 15×15 grid, building and demolishing free. Does adding the rooms one at a time end worse than
adding all the remaining rooms at once to the same house? And does the answer depend on the house the agents start
from: one that grew under a tight budget, or one that grew without cost constraints?

## Design

* World: houses on a **15×15 grid** (225 cells, rows A to O), hallways allowed, building and demolishing free; the
  hard rules and four scores of `docs/study-design.md`.
* Model: Claude Sonnet 5.5 at **medium** effort; a fresh agent per call, no tools, no memory, no feedback; the same
  Claude Code version for every call, recorded with it.
* Prompt: `house/prompt_template_100_rooms.txt`, the prompt of the priced runs with hallways
  (`house/prompt_template_hallways.txt` at commit `25e3cef`) with the cost section taken out, the grid size set to 15,
  and one line added after the room types: "Room ids: R followed by a number, as in R1, R2, R3."
* Four seed houses of 70 rooms (living room, kitchen, 34 bedrooms, 34 bathrooms), made in code, not by agents. Each
  starts from the 11-room house that ended one chain of the priced runs (Section 7 of the report) and grew one room at
  a time on the 15×15 grid:
  * Houses 1 and 2 grew under a tight budget: each room was added the way one of the priced runs' agents added a
    room, that is the same kind of change, next to the same type of room, as near the entrance, its cell touching as
    many rooms. House 1 starts from chain 1 of the priced run, house 2 from chain 4 of its repeat.
  * Houses 3 and 4 grew without cost constraints: of every five rooms, in a random order, three were added by the
    change that gave the best scores over the whole house, one by the change that gave the best scores over the rooms
    within two cells of it, and one by a change chosen at random. Scores were ranked corridor rooms first, then
    privacy order, walking distance and compactness. Houses 3 and 4 start from chains 3 and 5 of the priced run.
  * Of each kind, 12 candidates were grown, one from each priced-run chain. Each candidate was finished to 100 rooms
    10 times by each of four simulated builders (the three above, and one copying the agents of the paper's first
    run). The two chosen of each kind are those whose finished houses varied most in corridor rooms: the houses whose
    outcome depends most on how they are extended.
  * The seed houses and the code that made them are saved with the data, in `runs_100_rooms/seeds/`.
* Each chain starts from one seed house and has two kinds of agent:
  * **One room at a time:** steps 1 to 30 each add one room to the house the previous step left (the seed house for
    step 1): `add: bedroom`, `add: bathroom` and so on in turn. After step 30 the house has 100 rooms (49 bedrooms,
    49 bathrooms).
  * **All at once:** from the house left after each of steps 0 to 28 (step 0 is the seed house), one agent adds all
    the rooms still missing in a single request, such as `add: bedroom x15, bathroom x15` from step 0. After step 29
    the one room missing would be the same request as step 30.

  A chain has 59 calls.
* **3 chains per seed house, 12 in all**, run one chain at a time: chain 1 on houses 1, 2, 3 and 4, then chain 2 on
  houses 1 to 4, then chain 3 on houses 1 to 4. Within a chain the calls run in this order: all at once from step 0,
  step 1, all at once from step 1, step 2, and so on.
* A failed call (script rejected or house invalid) is retried with a fresh agent, up to 3 tries. If a one-room step
  still fails, that chain's one-room steps stop, and the all-at-once calls from the steps already reached are still
  made. A reply cut off by the output limit is recorded as cut off, not as an invalid house.
* No agent builds the 100-room house from scratch.
* Data in `runs_100_rooms/`.

## Expectations (stated beforehand)

1. As in the paper's free runs, the house after step 30 scores no worse than the house built all at once from step 0.

## Analyses

1. Descriptive: for the house after step 30 and the house built all at once from step 0, for each score: n,
   mean ± SD, median and range, overall and per seed house; the number of hallways in each.
2. For each score, an exact two-sided permutation test of the difference of means, the house after step 30 against
   the house built all at once from step 0 (4 tests), groups treated as independent. Reported uncorrected, with the
   Bonferroni threshold 0.05 / 4 = 0.0125. The 12 chains come from 4 seed houses, so chains on one house are not
   independent; this is reported with the results.
3. Corridor rooms: an exact rank-sum test, the same two groups.
4. Along the chain: for each score, the house after each one-room step and the house built all at once from each
   step, against the step; described, not tested.
5. Seed houses: analyses 1 and 4 for each seed house and for each kind of seed house; described, not tested (two
   houses of each kind).
6. What the agents changed: the share of the house they received still in place after each call (same cell, same
   room type), the number of rooms each script removed, and the number of hallways it added; per kind of agent.
7. Completion: failed calls per kind of agent, split by cause (script rejected, house invalid, reply cut off).
8. Tokens and cost of the agent calls per kind of agent.
