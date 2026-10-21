# Agentic housing

**Do AI agents make a design worse when they extend it one change at a time?**

A controlled experiment with AI coding agents, in a small world where design quality can be measured exactly:
houses on a grid.

**[Read the report](REPORT.md)** · [Study design](docs/study-design.md) · [Running the experiment](docs/running-the-experiment.md)

## The question

Software is rarely designed once. It grows through a long series of change requests, and each change tends to be
made where it is most convenient. A common belief is that a system grown this way ends up worse designed than one
built in one go for the same final requirements, even when nothing stops whoever makes each change from redesigning.
AI coding agents now make many of those changes. Do they patch locally, and does the design suffer for it?

Software design is hard to measure, so the question is asked in a world where design can be measured: single-floor
houses on a 5×5 grid, standing in for programs. Rooms must be reachable, doors join them, and familiar principles say
what makes a good house: bedrooms and bathrooms are not passages, public rooms sit near the entrance, nothing sticks
out.

## How it works

- **A small language.** An agent designs a house by writing a script: place or remove a room, add or remove a door
  or a window.
- **Validity.** Every house is checked against hard rules: a person can walk in through the front door, reach every
  room and walk back out. This is the house's equivalent of "the code runs".
- **Quality.** Valid houses get four scores, computed without human judgement: how often you must walk through a room
  that is not your destination, whether private rooms sit further in than public ones, how many doors apart the rooms
  are, and how compact the outline is.
- **Patching versus planning.** In each chain, a first agent builds a small house, and seven more agents each add one
  room to the house the previous agent left. Another agent plans the final house from scratch, and one more adds all
  seven rooms to the first house in a single request. Every agent is fresh: it gets the current house and one request,
  gives one reply, and never sees a score.

## What we found

- While building and demolishing cost nothing, patching never ended worse than planning. The agents attached new
  rooms while that worked and redesigned, up to rebuilding the whole house, when it did not. They showed no built-in
  preference for local changes.
- Taking away hallways, or lowering the agents' reasoning effort, did not change that.
- When every change had a price, patching one room at a time did end worse, in both runs that tested it. The patching
  agents mostly bought the cheapest change, a room and a door, rather than the hallway later rooms would need. Agents
  that saw all the requirements at once built the hallway.

Local patching came from the price of change, combined with requirements that arrive one at a time.

The two houses below come from a typical chain of a run in which every change had a price (the chain whose corridor
score is nearest the run's median). On the left is the house after seven agents had each added one room; on the
right, a house planned from scratch for the same rooms. Both are valid. In the planned house every bedroom and
bathroom opens off the living room or a central hallway; in the patched one, several are reached only by walking
through another bedroom or bathroom.
`[ENTRY]` is the entrance and `-[   ]-` a door; a gap on a cell's bottom line in a vertical wall is a door.

```
H (chain 2)                                   I (chain 2)
VALID                                         VALID

      1       2       3       4       5             1       2       3       4       5
  +-------+[ENTRY]+-------+-------+                     +-------+[ENTRY]+-------+
  |   R2  |   R1  |   R3  |  R13  |                     |   R2  |   R1  |   R3  |
A |kitchen| living|bedroom|bedroom|           A         |kitchen| living|bedroom|
  |                               |                     |                       |
  +-------+-[   ]-+-------+-------+                     +-------+-[   ]-+-------+
  |   R8  |   R5  |   R7  |  R11  |                     |   R8  |   R4  |   R9  |
B |  bath |hallway|bedroom|bedroom|           B         |bedroom|hallway|bedroom|
  |                               |                     |                       |
  +-------+-[   ]-+-------+-------+                     +-------+-[   ]-+-------+
  |  R10  |   R6  |   R9  |                             |  R10  |   R5  |  R11  |
C |  bath |  bath |bedroom|                   C         |bedroom|hallway|bedroom|
  |                       |                             |                       |
  +-------+-------+-[   ]-+                             +-------+-[   ]-+-------+
                  |  R12  |                             |  R12  |   R6  |  R13  |
D                 |  bath |                   D         |  bath |hallway|  bath |
                  |       |                             |                       |
                  +-------+                             +-------+-[   ]-+-------+
                                                        |  R14  |   R7  |  R15  |
E                                             E         |  bath |hallway|  bath |
                                                        |                       |
                                                        +-------+-------+-------+

corridor rooms    6                           corridor rooms    0
privacy order     0.03                        privacy order     0.03
walking distance  2.88                        walking distance  3.05
compactness       2                           compactness       0
```

## The runs

Every run used Claude Sonnet 5.5 in six chains, and each had its analysis plan written before its first agent call.

| Run | What changed | Did patching end worse? | Report |
|---|---|---|---|
| 1 | hallways allowed, nothing costs | no | Sections 1–4 |
| 2 | no hallways | no | Section 5 |
| 3 | no hallways, low reasoning effort | no | Section 6 |
| 4 | no hallways, every change has a price | no | Section 7 |
| 5 | hallways allowed, every change has a price (run twice) | yes, one room at a time; not in one go | Section 7 |

The code, analysis plan and data folder of each run are listed in
[running the experiment](docs/running-the-experiment.md#the-runs-in-the-report).

## Repository

```
REPORT.md                        the report, generated from the data by paper/build_report.py
docs/study-design.md             the house world (language, rules, scores) and the experiment design
docs/running-the-experiment.md   setup, running the agents, the code, plan and data of each run
house/                           the house language: interpreter, rules, scores, drawings, server, agent runner
paper/                           the report template and generator, and the analysis plans
runs*/                           the data: one record per script sent, and the agents' raw replies
examples/                        example layouts
tests/                           the test suite
```

## Quick start

Python 3.9 or later, standard library only; the tests need pytest. Running agents needs the Claude Code CLI.

```
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest -q                                                          # tests
.venv/bin/python -m house.render examples/example_house.txt examples/chain_house.txt   # draw two houses
.venv/bin/python paper/build_report.py                                                 # rebuild REPORT.md
```

## Authors

Nuno Oliveira, with Claude Opus 5.5.
