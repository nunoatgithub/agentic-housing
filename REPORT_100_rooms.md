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
single one-room step, and left them with fewer passages than it found. At this size, whether a house was redesigned
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
  2.1.310). Run 2: eight chains of Sonnet 5.5, two per seed house (Claude Code 2.1.311, 2.1.312, 2.1.314), and four of
  GPT-6 Luna at medium effort, one per seed house (GitHub Copilot CLI 1.0.105). The two models are reported separately.

Both runs are described, not tested. Lower is better for every score. Corridor rooms counts the kitchens, bedrooms and
bathrooms that someone must walk through to reach another room.

## 3. Run 1: hallways can be built

### 3.1 The houses at the end

| Seed house | Chain | Model      | House                    | Corridor rooms | Privacy order | Walking distance | Compactness |
| ---------- | ----- | ---------- | ------------------------ | -------------- | ------------- | ---------------- | ----------- |
| 1          |       |            | seed house (70 rooms)    | 39             | 0.0037        | 9.56             | 8           |
|            | 1     | Sonnet 5.5 | after step 30            | 56             | 0.0026        | 11.43            | 14          |
|            | 1     | Sonnet 5.5 | all at once from step 0  | 39             | 0.0026        | 15.22            | 28          |
|            | 1     | Sonnet 5.5 | all at once from step 15 | 45             | 0.0026        | 13.68            | 26          |
| 2          |       |            | seed house (70 rooms)    | 39             | 0.0037        | 9.91             | 12          |
|            | 2     | Sonnet 5.5 | after step 30            | 55             | 0.0026        | 12.66            | 20          |
|            | 2     | Sonnet 5.5 | all at once from step 0  | 39             | 0.0026        | 14.91            | 34          |
|            | 2     | Sonnet 5.5 | all at once from step 15 | 49             | 0.0026        | 13.23            | 22          |
| 3          |       |            | seed house (70 rooms)    | 6              | 0.0074        | 7.96             | 16          |
|            | 3     | Sonnet 5.5 | after step 30            | 14             | 0.0051        | 10.40            | 28          |
|            | 3     | Sonnet 5.5 | all at once from step 0  | 7              | 0.0051        | 14.47            | 16          |
|            | 3     | Sonnet 5.5 | all at once from step 15 | 10             | 0.0051        | 11.37            | 18          |
| 4          |       |            | seed house (70 rooms)    | 5              | 0.0074        | 7.60             | 8           |
|            | 4     | Sonnet 5.5 | after step 30            | 15             | 0.0051        | 9.53             | 12          |
|            | 4     | Sonnet 5.5 | all at once from step 0  | 5              | 0.0051        | 10.60            | 32          |
|            | 4     | Sonnet 5.5 | all at once from step 15 | 8              | 0.0051        | 10.04            | 14          |

Before the run we expected the house after step 30 to score no worse than the house built all at once from step 0, as
on the small grid. That held for walking distance, which was lower after step 30 in every seed house, and for
compactness in three of the four. It failed for corridor rooms, which was higher after step 30 in every
seed house. The all-at-once agents from step 0 left corridor rooms exactly where the seed house had it in
three houses, and one higher in the other. Privacy order was the same in every 100-room house of
a seed house. The scores of every step are in Appendix A.

### 3.2 What the agents changed

| Model      | Agent              | Calls | Calls that removed a room | Most rooms removed by one call | Least share of the house kept | Hallways added per call |
| ---------- | ------------------ | ----- | ------------------------- | ------------------------------ | ----------------------------- | ----------------------- |
| Sonnet 5.5 | One room at a time | 120   | 35                        | 1                              | 98.7%                         | 0.33                    |
| Sonnet 5.5 | All at once        | 116   | 78                        | 3                              | 97.5%                         | 10.47                   |

No agent rebuilt the house. A one-room step removed at most one room, and an all-at-once call kept at least
97.5% of the house it received. The difference between the two kinds of agent was in what they added: a
one-room step added 0.33 hallways on average, an all-at-once call 10.47.

### 3.3 Why it happens

An all-at-once agent sees every missing room, so it can lay out a hallway that serves them all. It hung that hallway
wing behind the house it received and joined the new rooms to it. Almost none of the new rooms became a passage, so corridor
rooms stayed where the house had it; but the wing lies beyond the old house, so every room in it is further from
everything else, and the walk got longer. A one-room agent sees one room. A hallway for one room is rarely worth it,
so it mostly attached the room to a room already there, and every time that room was a bedroom or bathroom with
nothing else in front of it, a new passage was made. Over 30 steps those passages added up.

### 3.4 Failed calls and cost

| Model      | Agent              | Tries | Valid | Script rejected | House invalid | Reply cut off | Output tokens per try | Cost per try |
| ---------- | ------------------ | ----- | ----- | --------------- | ------------- | ------------- | --------------------- | ------------ |
| Sonnet 5.5 | One room at a time | 129   | 120   | 7               | 2             | 0             | 925                   | $0.025       |
| Sonnet 5.5 | All at once        | 123   | 116   | 2               | 5             | 0             | 2661                  | $0.043       |

Every failed call was tried again with a fresh agent and succeeded within three tries; every chain has all 59 houses.

## 4. Run 2: no hallway can be built

### 4.1 The houses at the end

Sonnet 5.5:

| Seed house | Chain | Model      | House                    | Corridor rooms | Privacy order | Walking distance | Compactness |
| ---------- | ----- | ---------- | ------------------------ | -------------- | ------------- | ---------------- | ----------- |
| 1          |       |            | seed house (70 rooms)    | 39             | 0.0037        | 9.56             | 8           |
|            | 1     | Sonnet 5.5 | after step 30            | 60             | 0.0026        | 11.89            | 12          |
|            | 1     | Sonnet 5.5 | all at once from step 0  | 61             | 0.0026        | 11.69            | 10          |
|            | 1     | Sonnet 5.5 | all at once from step 15 | 62             | 0.0026        | 11.92            | 10          |
|            | 9     | Sonnet 5.5 | after step 30            | 59             | 0.0026        | 12.00            | 12          |
|            | 9     | Sonnet 5.5 | all at once from step 0  | 64             | 0.0026        | 11.69            | 10          |
|            | 9     | Sonnet 5.5 | all at once from step 15 | 59             | 0.0026        | 12.22            | 14          |
| 2          |       |            | seed house (70 rooms)    | 39             | 0.0037        | 9.91             | 12          |
|            | 2     | Sonnet 5.5 | after step 30            | 62             | 0.0026        | 12.61            | 18          |
|            | 2     | Sonnet 5.5 | all at once from step 0  | 62             | 0.0026        | 13.13            | 26          |
|            | 2     | Sonnet 5.5 | all at once from step 15 | 53             | 0.0026        | 12.43            | 14          |
|            | 10    | Sonnet 5.5 | after step 30            | 65             | 0.0026        | 12.51            | 14          |
|            | 10    | Sonnet 5.5 | all at once from step 0  | 64             | 0.0026        | 12.05            | 8           |
|            | 10    | Sonnet 5.5 | all at once from step 15 | 65             | 0.0026        | 12.15            | 8           |
| 3          |       |            | seed house (70 rooms)    | 6              | 0.0074        | 7.96             | 16          |
|            | 3     | Sonnet 5.5 | after step 30            | 32             | 0.0051        | 9.04             | 8           |
|            | 3     | Sonnet 5.5 | all at once from step 0  | 24             | 0.0051        | 10.65            | 18          |
|            | 3     | Sonnet 5.5 | all at once from step 15 | 33             | 0.0051        | 9.06             | 8           |
|            | 11    | Sonnet 5.5 | after step 30            | 33             | 0.0051        | 8.95             | 2           |
|            | 11    | Sonnet 5.5 | all at once from step 0  | 33             | 0.0051        | 8.99             | 18          |
|            | 11    | Sonnet 5.5 | all at once from step 15 | 34             | 0.0051        | 8.98             | 10          |
| 4          |       |            | seed house (70 rooms)    | 5              | 0.0074        | 7.60             | 8           |
|            | 4     | Sonnet 5.5 | after step 30            | 30             | 0.0051        | 8.65             | 0           |
|            | 4     | Sonnet 5.5 | all at once from step 0  | 35             | 0.0051        | 8.72             | 8           |
|            | 4     | Sonnet 5.5 | all at once from step 15 | 31             | 0.0051        | 8.65             | 0           |
|            | 12    | Sonnet 5.5 | after step 30            | 29             | 0.0051        | 8.84             | 4           |
|            | 12    | Sonnet 5.5 | all at once from step 0  | 35             | 0.0051        | 8.72             | 8           |
|            | 12    | Sonnet 5.5 | all at once from step 15 | 29             | 0.0051        | 8.73             | 2           |

GPT-6 Luna:

| Seed house | Chain | Model      | House                    | Corridor rooms | Privacy order | Walking distance | Compactness |
| ---------- | ----- | ---------- | ------------------------ | -------------- | ------------- | ---------------- | ----------- |
| 1          |       |            | seed house (70 rooms)    | 39             | 0.0037        | 9.56             | 8           |
|            | 5     | GPT-6 Luna | after step 30            | 22             | 0.0026        | 8.08             | 10          |
|            | 5     | GPT-6 Luna | all at once from step 0  | 24             | 0.0026        | 9.82             | 8           |
|            | 5     | GPT-6 Luna | all at once from step 15 | 22             | 0.0026        | 7.76             | 8           |
| 2          |       |            | seed house (70 rooms)    | 39             | 0.0037        | 9.91             | 12          |
|            | 6     | GPT-6 Luna | after step 30            | 22             | 0.0026        | 8.13             | 6           |
|            | 6     | GPT-6 Luna | all at once from step 0  | 37             | 0.0026        | 12.31            | 24          |
|            | 6     | GPT-6 Luna | all at once from step 15 | 8              | 0.0026        | 7.79             | 0           |
| 3          |       |            | seed house (70 rooms)    | 6              | 0.0074        | 7.96             | 16          |
|            | 7     | GPT-6 Luna | after step 30            | 30             | 0.0051        | 10.87            | 10          |
|            | 7     | GPT-6 Luna | all at once from step 0  | 36             | 0.0051        | 13.84            | 18          |
|            | 7     | GPT-6 Luna | all at once from step 15 | 28             | 0.0051        | 9.85             | 10          |
| 4          |       |            | seed house (70 rooms)    | 5              | 0.0074        | 7.60             | 8           |
|            | 8     | GPT-6 Luna | after step 30            | 29             | 0.0051        | 10.06            | 22          |
|            | 8     | GPT-6 Luna | all at once from step 0  | 22             | 0.0051        | 9.78             | 14          |
|            | 8     | GPT-6 Luna | all at once from step 15 | 30             | 0.0051        | 10.44            | 16          |

One call has no valid house: the all-at-once call from step 5 in house 2, chain 6 (GPT-6 Luna), whose three tries were all rejected; the chain went on without it. The
scores of every step are in Appendix B.

Across the eight Sonnet chains, the house after step 30 had fewer corridor rooms than the house built all at
once from step 0 in four chains and more in two; it was shorter to walk in
four and longer in four. Across the four GPT-6 Luna chains, the house after
step 30 had fewer corridor rooms in three and more in one; it was shorter to walk in
three and longer in one.

The seed house mattered most for GPT-6 Luna. In the two budget houses, every Sonnet chain ended with more corridor
rooms than the seed house had, and GPT-6 Luna ended with fewer. In the two planned houses, every chain of both models
ended with more.

### 4.2 What the agents changed

| Model      | Agent              | Calls | Calls that removed a room | Most rooms removed by one call | Least share of the house kept |
| ---------- | ------------------ | ----- | ------------------------- | ------------------------------ | ----------------------------- |
| Sonnet 5.5 | One room at a time | 240   | 6                         | 1                              | 99.2%                         |
| Sonnet 5.5 | All at once        | 232   | 0                         | 0                              | 100.0%                        |
| GPT-6 Luna | One room at a time | 120   | 14                        | 45                             | 43.8%                         |
| GPT-6 Luna | All at once        | 115   | 11                        | 42                             | 45.5%                         |

Sonnet 5.5 changed almost nothing it was given. No all-at-once call removed a room. Of 240 one-room
steps, six removed one room each, all in the planned houses: five a
seed hallway and one a bathroom. No one-room step added more than one door beyond those of its new room.

GPT-6 Luna changed the house in two ways. In 11 of its 235 calls
(nine of them all at once) it added ten or more doors beyond those of its new rooms, opening up the
house it received, in seven of them without removing a room; the biggest was
step 6 of house 1, chain 5 (GPT-6 Luna), which added 57 doors and cut corridor rooms from 44 to
2. And six calls removed a quarter of the house or more, one
of them a one-room step, all in the budget houses. In each budget house one one-room step, step
6, redesigned the house, and the later steps built on that design.

### 4.3 Why it happens

Without hallways, a new room can only be reached through a room already there, so every addition risks a passage. An
all-at-once agent no longer has a hallway wing to hang the new rooms on, so it attaches them one after another just as
the one-room agents do, and neither kind of house comes out ahead. Sonnet did that and nothing else: it took the house as
given and attached rooms to it. The budget houses arrived with many passages, kept them, and gained more.

The way out of a passage is another way in: a second door, or a room rebuilt. GPT-6 Luna took it. It opened extra
doors between rooms that were already there, and in the budget houses it took apart large parts of the house and laid
them out again. It did so mostly when it saw all the rooms at once, but a single one-room step was enough to redesign a
budget house, so the order in which the rooms arrived did not decide whether the house was redesigned; the model did.

### 4.4 Failed calls and cost

| Model      | Agent              | Tries | Valid | Script rejected | House invalid | Reply cut off | Output tokens per try | Cost per try |
| ---------- | ------------------ | ----- | ----- | --------------- | ------------- | ------------- | --------------------- | ------------ |
| Sonnet 5.5 | One room at a time | 246   | 240   | 4               | 2             | 0             | 804                   | $0.024       |
| Sonnet 5.5 | All at once        | 235   | 232   | 1               | 2             | 0             | 1703                  | $0.034       |
| GPT-6 Luna | One room at a time | 134   | 120   | 7               | 7             | 0             | not reported          | not reported |
| GPT-6 Luna | All at once        | 143   | 115   | 19              | 5             | 4             | not reported          | not reported |

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
the rooms at once, but also in a single one-room step. In neither case did the order in which the rooms arrived decide whether the house got
redesigned.

## Appendix A. Run 1, step by step

Each row is one kind of house in one chain: the house after the step, or the house built all at once from the house
after that step. Step 0 of "after the step" is the seed house. All-at-once calls start from steps 0 to 28, so step 30
has none.

**Corridor rooms**

| Chain | Seed house | Model      | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | ---------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5 | after the step            | 39     | 40     | 41      | 44      | 47      | 51      | 56      |
| 1     | 1          | Sonnet 5.5 | all at once from the step | 39     | 39     | 42      | 45      | 48      | 51      | –       |
| 2     | 2          | Sonnet 5.5 | after the step            | 39     | 42     | 46      | 49      | 52      | 55      | 55      |
| 2     | 2          | Sonnet 5.5 | all at once from the step | 39     | 43     | 46      | 49      | 53      | 60      | –       |
| 3     | 3          | Sonnet 5.5 | after the step            | 6      | 8      | 8       | 10      | 13      | 14      | 14      |
| 3     | 3          | Sonnet 5.5 | all at once from the step | 7      | 8      | 8       | 10      | 13      | 14      | –       |
| 4     | 4          | Sonnet 5.5 | after the step            | 5      | 5      | 6       | 8       | 9       | 11      | 15      |
| 4     | 4          | Sonnet 5.5 | all at once from the step | 5      | 5      | 6       | 8       | 9       | 11      | –       |

**Privacy order**

| Chain | Seed house | Model      | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | ---------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5 | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 1     | 1          | Sonnet 5.5 | all at once from the step | 0.0026 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 2     | 2          | Sonnet 5.5 | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 2     | 2          | Sonnet 5.5 | all at once from the step | 0.0026 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 3     | 3          | Sonnet 5.5 | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0054  | 0.0051  |
| 3     | 3          | Sonnet 5.5 | all at once from the step | 0.0051 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0051  | –       |
| 4     | 4          | Sonnet 5.5 | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0054  | 0.0051  |
| 4     | 4          | Sonnet 5.5 | all at once from the step | 0.0051 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0051  | –       |

**Walking distance**

| Chain | Seed house | Model      | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | ---------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5 | after the step            | 9.56   | 9.91   | 10.36   | 10.67   | 10.87   | 11.17   | 11.43   |
| 1     | 1          | Sonnet 5.5 | all at once from the step | 15.22  | 13.22  | 12.13   | 13.68   | 12.85   | 11.48   | –       |
| 2     | 2          | Sonnet 5.5 | after the step            | 9.91   | 10.36  | 10.94   | 11.38   | 11.77   | 12.24   | 12.66   |
| 2     | 2          | Sonnet 5.5 | all at once from the step | 14.91  | 15.37  | 14.15   | 13.23   | 13.09   | 12.62   | –       |
| 3     | 3          | Sonnet 5.5 | after the step            | 7.96   | 8.24   | 8.80    | 9.18    | 9.56    | 10.01   | 10.40   |
| 3     | 3          | Sonnet 5.5 | all at once from the step | 14.47  | 11.32  | 13.71   | 11.37   | 10.42   | 10.61   | –       |
| 4     | 4          | Sonnet 5.5 | after the step            | 7.60   | 8.01   | 8.29    | 8.67    | 8.97    | 9.35    | 9.53    |
| 4     | 4          | Sonnet 5.5 | all at once from the step | 10.60  | 10.71  | 10.13   | 10.04   | 9.78    | 9.82    | –       |

**Compactness**

| Chain | Seed house | Model      | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | ---------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5 | after the step            | 8      | 10     | 14      | 14      | 16      | 14      | 14      |
| 1     | 1          | Sonnet 5.5 | all at once from the step | 28     | 28     | 24      | 26      | 24      | 18      | –       |
| 2     | 2          | Sonnet 5.5 | after the step            | 12     | 10     | 12      | 14      | 20      | 20      | 20      |
| 2     | 2          | Sonnet 5.5 | all at once from the step | 34     | 28     | 28      | 22      | 30      | 20      | –       |
| 3     | 3          | Sonnet 5.5 | after the step            | 16     | 16     | 20      | 24      | 24      | 26      | 28      |
| 3     | 3          | Sonnet 5.5 | all at once from the step | 16     | 28     | 38      | 18      | 20      | 24      | –       |
| 4     | 4          | Sonnet 5.5 | after the step            | 8      | 6      | 10      | 10      | 8       | 14      | 12      |
| 4     | 4          | Sonnet 5.5 | all at once from the step | 32     | 34     | 26      | 14      | 14      | 14      | –       |

## Appendix B. Run 2, step by step

As in Appendix A.

**Corridor rooms**

| Chain | Seed house | Model      | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | ---------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5 | after the step            | 39     | 43     | 47      | 51      | 55      | 57      | 60      |
| 1     | 1          | Sonnet 5.5 | all at once from the step | 61     | 64     | 63      | 62      | 63      | 61      | –       |
| 2     | 2          | Sonnet 5.5 | after the step            | 39     | 43     | 47      | 51      | 54      | 58      | 62      |
| 2     | 2          | Sonnet 5.5 | all at once from the step | 62     | 65     | 63      | 53      | 61      | 63      | –       |
| 3     | 3          | Sonnet 5.5 | after the step            | 6      | 11     | 14      | 19      | 23      | 28      | 32      |
| 3     | 3          | Sonnet 5.5 | all at once from the step | 24     | 34     | 34      | 33      | 18      | 32      | –       |
| 4     | 4          | Sonnet 5.5 | after the step            | 5      | 10     | 15      | 18      | 23      | 27      | 30      |
| 4     | 4          | Sonnet 5.5 | all at once from the step | 35     | 31     | 33      | 31      | 32      | 31      | –       |
| 9     | 1          | Sonnet 5.5 | after the step            | 39     | 43     | 48      | 51      | 54      | 56      | 59      |
| 9     | 1          | Sonnet 5.5 | all at once from the step | 64     | 64     | 61      | 59      | 60      | 60      | –       |
| 10    | 2          | Sonnet 5.5 | after the step            | 39     | 43     | 48      | 52      | 57      | 60      | 65      |
| 10    | 2          | Sonnet 5.5 | all at once from the step | 64     | 61     | 65      | 65      | 63      | 64      | –       |
| 11    | 3          | Sonnet 5.5 | after the step            | 6      | 11     | 16      | 20      | 25      | 30      | 33      |
| 11    | 3          | Sonnet 5.5 | all at once from the step | 33     | 33     | 33      | 34      | 33      | 34      | –       |
| 12    | 4          | Sonnet 5.5 | after the step            | 5      | 10     | 14      | 18      | 22      | 25      | 29      |
| 12    | 4          | Sonnet 5.5 | all at once from the step | 35     | 12     | 31      | 29      | 32      | 30      | –       |
| 5     | 1          | GPT-6 Luna | after the step            | 39     | 44     | 6       | 10      | 14      | 19      | 22      |
| 5     | 1          | GPT-6 Luna | all at once from the step | 24     | 67     | 19      | 22      | 22      | 21      | –       |
| 6     | 2          | GPT-6 Luna | after the step            | 39     | 44     | 4       | 9       | 14      | 17      | 22      |
| 6     | 2          | GPT-6 Luna | all at once from the step | 37     | –      | 19      | 8       | 24      | 0       | –       |
| 7     | 3          | GPT-6 Luna | after the step            | 6      | 13     | 14      | 19      | 23      | 26      | 30      |
| 7     | 3          | GPT-6 Luna | all at once from the step | 36     | 18     | 16      | 28      | 31      | 31      | –       |
| 8     | 4          | GPT-6 Luna | after the step            | 5      | 9      | 13      | 17      | 21      | 24      | 29      |
| 8     | 4          | GPT-6 Luna | all at once from the step | 22     | 27     | 33      | 30      | 29      | 29      | –       |

**Privacy order**

| Chain | Seed house | Model      | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | ---------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5 | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 1     | 1          | Sonnet 5.5 | all at once from the step | 0.0026 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 2     | 2          | Sonnet 5.5 | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 2     | 2          | Sonnet 5.5 | all at once from the step | 0.0026 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 3     | 3          | Sonnet 5.5 | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0054  | 0.0051  |
| 3     | 3          | Sonnet 5.5 | all at once from the step | 0.0051 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0051  | –       |
| 4     | 4          | Sonnet 5.5 | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0054  | 0.0051  |
| 4     | 4          | Sonnet 5.5 | all at once from the step | 0.0051 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0051  | –       |
| 9     | 1          | Sonnet 5.5 | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 9     | 1          | Sonnet 5.5 | all at once from the step | 0.0026 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 10    | 2          | Sonnet 5.5 | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 10    | 2          | Sonnet 5.5 | all at once from the step | 0.0026 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 11    | 3          | Sonnet 5.5 | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0054  | 0.0051  |
| 11    | 3          | Sonnet 5.5 | all at once from the step | 0.0051 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0051  | –       |
| 12    | 4          | Sonnet 5.5 | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0054  | 0.0051  |
| 12    | 4          | Sonnet 5.5 | all at once from the step | 0.0051 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0051  | –       |
| 5     | 1          | GPT-6 Luna | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 5     | 1          | GPT-6 Luna | all at once from the step | 0.0026 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 6     | 2          | GPT-6 Luna | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 6     | 2          | GPT-6 Luna | all at once from the step | 0.0026 | –      | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 7     | 3          | GPT-6 Luna | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0054  | 0.0051  |
| 7     | 3          | GPT-6 Luna | all at once from the step | 0.0051 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0051  | –       |
| 8     | 4          | GPT-6 Luna | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0054  | 0.0051  |
| 8     | 4          | GPT-6 Luna | all at once from the step | 0.0051 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0051  | –       |

**Walking distance**

| Chain | Seed house | Model      | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | ---------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5 | after the step            | 9.56   | 10.01  | 10.52   | 10.89   | 11.24   | 11.54   | 11.89   |
| 1     | 1          | Sonnet 5.5 | all at once from the step | 11.69  | 12.23  | 12.30   | 11.92   | 11.75   | 11.75   | –       |
| 2     | 2          | Sonnet 5.5 | after the step            | 9.91   | 10.32  | 10.79   | 11.28   | 11.72   | 12.20   | 12.61   |
| 2     | 2          | Sonnet 5.5 | all at once from the step | 13.13  | 12.38  | 12.19   | 12.43   | 12.52   | 12.48   | –       |
| 3     | 3          | Sonnet 5.5 | after the step            | 7.96   | 8.30   | 8.48    | 8.58    | 8.77    | 8.85    | 9.04    |
| 3     | 3          | Sonnet 5.5 | all at once from the step | 10.65  | 8.99   | 8.97    | 9.06    | 8.85    | 9.00    | –       |
| 4     | 4          | Sonnet 5.5 | after the step            | 7.60   | 7.80   | 7.99    | 8.17    | 8.39    | 8.52    | 8.65    |
| 4     | 4          | Sonnet 5.5 | all at once from the step | 8.72   | 8.67   | 8.58    | 8.65    | 8.72    | 8.71    | –       |
| 9     | 1          | Sonnet 5.5 | after the step            | 9.56   | 10.01  | 10.46   | 10.81   | 11.20   | 11.69   | 12.00   |
| 9     | 1          | Sonnet 5.5 | all at once from the step | 11.69  | 11.67  | 11.98   | 12.22   | 11.67   | 12.11   | –       |
| 10    | 2          | Sonnet 5.5 | after the step            | 9.91   | 10.31  | 10.68   | 11.12   | 11.50   | 11.98   | 12.51   |
| 10    | 2          | Sonnet 5.5 | all at once from the step | 12.05  | 12.78  | 12.13   | 12.15   | 12.17   | 12.47   | –       |
| 11    | 3          | Sonnet 5.5 | after the step            | 7.96   | 8.16   | 8.35    | 8.44    | 8.59    | 8.74    | 8.95    |
| 11    | 3          | Sonnet 5.5 | all at once from the step | 8.99   | 9.04   | 8.97    | 8.98    | 8.86    | 8.89    | –       |
| 12    | 4          | Sonnet 5.5 | after the step            | 7.60   | 7.81   | 8.03    | 8.18    | 8.41    | 8.66    | 8.84    |
| 12    | 4          | Sonnet 5.5 | all at once from the step | 8.72   | 8.93   | 8.61    | 8.73    | 8.75    | 8.87    | –       |
| 5     | 1          | GPT-6 Luna | after the step            | 9.56   | 10.12  | 7.04    | 7.26    | 7.66    | 7.86    | 8.08    |
| 5     | 1          | GPT-6 Luna | all at once from the step | 9.82   | 12.87  | 8.07    | 7.76    | 8.20    | 8.06    | –       |
| 6     | 2          | GPT-6 Luna | after the step            | 9.91   | 10.43  | 6.15    | 6.65    | 7.47    | 7.80    | 8.13    |
| 6     | 2          | GPT-6 Luna | all at once from the step | 12.31  | –      | 7.09    | 7.79    | 8.01    | 6.67    | –       |
| 7     | 3          | GPT-6 Luna | after the step            | 7.96   | 8.27   | 9.03    | 9.28    | 10.48   | 10.70   | 10.87   |
| 7     | 3          | GPT-6 Luna | all at once from the step | 13.84  | 8.97   | 10.71   | 9.85    | 10.53   | 10.66   | –       |
| 8     | 4          | GPT-6 Luna | after the step            | 7.60   | 7.94   | 8.50    | 8.91    | 9.26    | 9.61    | 10.06   |
| 8     | 4          | GPT-6 Luna | all at once from the step | 9.78   | 8.89   | 12.81   | 10.44   | 9.74    | 9.81    | –       |

**Compactness**

| Chain | Seed house | Model      | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | ---------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5 | after the step            | 8      | 10     | 8       | 10      | 12      | 14      | 12      |
| 1     | 1          | Sonnet 5.5 | all at once from the step | 10     | 6      | 8       | 10      | 10      | 14      | –       |
| 2     | 2          | Sonnet 5.5 | after the step            | 12     | 10     | 12      | 18      | 16      | 18      | 18      |
| 2     | 2          | Sonnet 5.5 | all at once from the step | 26     | 10     | 12      | 14      | 16      | 16      | –       |
| 3     | 3          | Sonnet 5.5 | after the step            | 16     | 14     | 12      | 18      | 12      | 10      | 8       |
| 3     | 3          | Sonnet 5.5 | all at once from the step | 18     | 4      | 14      | 8       | 12      | 10      | –       |
| 4     | 4          | Sonnet 5.5 | after the step            | 8      | 4      | 4       | 8       | 8       | 2       | 0       |
| 4     | 4          | Sonnet 5.5 | all at once from the step | 8      | 2      | 0       | 0       | 10      | 2       | –       |
| 9     | 1          | Sonnet 5.5 | after the step            | 8      | 10     | 10      | 14      | 14      | 14      | 12      |
| 9     | 1          | Sonnet 5.5 | all at once from the step | 10     | 8      | 22      | 14      | 14      | 14      | –       |
| 10    | 2          | Sonnet 5.5 | after the step            | 12     | 10     | 10      | 10      | 10      | 16      | 14      |
| 10    | 2          | Sonnet 5.5 | all at once from the step | 8      | 14     | 6       | 8       | 10      | 16      | –       |
| 11    | 3          | Sonnet 5.5 | after the step            | 16     | 14     | 16      | 12      | 4       | 4       | 2       |
| 11    | 3          | Sonnet 5.5 | all at once from the step | 18     | 14     | 8       | 10      | 2       | 2       | –       |
| 12    | 4          | Sonnet 5.5 | after the step            | 8      | 4      | 8       | 6       | 6       | 4       | 4       |
| 12    | 4          | Sonnet 5.5 | all at once from the step | 8      | 6      | 4       | 2       | 2       | 6       | –       |
| 5     | 1          | GPT-6 Luna | after the step            | 8      | 10     | 14      | 12      | 14      | 10      | 10      |
| 5     | 1          | GPT-6 Luna | all at once from the step | 8      | 12     | 12      | 8       | 14      | 8       | –       |
| 6     | 2          | GPT-6 Luna | after the step            | 12     | 18     | 0       | 0       | 0       | 2       | 6       |
| 6     | 2          | GPT-6 Luna | all at once from the step | 24     | –      | 2       | 0       | 0       | 0       | –       |
| 7     | 3          | GPT-6 Luna | after the step            | 16     | 16     | 14      | 16      | 18      | 10      | 10      |
| 7     | 3          | GPT-6 Luna | all at once from the step | 18     | 6      | 18      | 10      | 16      | 12      | –       |
| 8     | 4          | GPT-6 Luna | after the step            | 8      | 14     | 10      | 10      | 18      | 20      | 22      |
| 8     | 4          | GPT-6 Luna | all at once from the step | 14     | 8      | 22      | 16      | 16      | 24      | –       |

## Reproducibility

The data are in `runs_100_rooms/` (run 1) and `runs_100_rooms_no_hallways/` (run 2); every agent call is one JSON
record with its script, the house it produced, the house's scores and the agent's token usage. The seed houses and the
code that made them are in `runs_100_rooms/seeds/`. The chains were run with `python -m house.run_100_rooms` as
described in [running the experiment](docs/running-the-experiment.md#70-to-100-room-chains). This report is generated
by `python paper/build_report_100_rooms.py` from `paper/REPORT_100_rooms.template.md`.
