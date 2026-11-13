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

[Watch the videos](viewer/videos/watch.md)

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
  (Claude Code 2.1.310); eight in run 2, two per seed house (2.1.311, 2.1.312, 2.1.314); four in run 3
  (2.1.314, 2.1.319); four in run 4 (2.1.322); and two in run 5, houses 1 and 3 (2.1.322). GPT-6
  Luna at medium effort: four chains in run 2, one per seed house (GitHub Copilot CLI 1.0.105). DeepSeek flash
  (DeepSeek-V4.1-Flash-1017) at low thinking through a standalone adapter (version 1): two chains,
  houses 1 and 3, in runs 1, 3, 4 and 5. The models are reported separately.

The runs are described, not tested. Lower is better for every score. Corridor rooms counts the kitchens, bedrooms and
bathrooms that lie on a best route between two other rooms, a best route being one that crosses as few kitchens,
bedrooms and bathrooms as possible.

## 3. Run 1: hallways can be built

### 3.1 The houses at the end

Sonnet 5.5:

| Seed house | Chain | Model      | House                    | Corridor rooms | Privacy order | Walking distance | Compactness |
| ---------- | ----- | ---------- | ------------------------ | -------------- | ------------- | ---------------- | ----------- |
| 1          |       |            | seed house (70 rooms)    | 42             | 0.0037        | 9.56             | 8           |
|            | 1     | Sonnet 5.5 | after step 30            | 59             | 0.0026        | 11.43            | 14          |
|            | 1     | Sonnet 5.5 | all at once from step 0  | 42             | 0.0026        | 15.22            | 28          |
|            | 1     | Sonnet 5.5 | all at once from step 15 | 48             | 0.0026        | 13.68            | 26          |
| 2          |       |            | seed house (70 rooms)    | 42             | 0.0037        | 9.91             | 12          |
|            | 2     | Sonnet 5.5 | after step 30            | 57             | 0.0026        | 12.66            | 20          |
|            | 2     | Sonnet 5.5 | all at once from step 0  | 42             | 0.0026        | 14.91            | 34          |
|            | 2     | Sonnet 5.5 | all at once from step 15 | 51             | 0.0026        | 13.23            | 22          |
| 3          |       |            | seed house (70 rooms)    | 14             | 0.0074        | 7.96             | 16          |
|            | 3     | Sonnet 5.5 | after step 30            | 21             | 0.0051        | 10.40            | 28          |
|            | 3     | Sonnet 5.5 | all at once from step 0  | 15             | 0.0051        | 14.47            | 16          |
|            | 3     | Sonnet 5.5 | all at once from step 15 | 17             | 0.0051        | 11.37            | 18          |
| 4          |       |            | seed house (70 rooms)    | 13             | 0.0074        | 7.60             | 8           |
|            | 4     | Sonnet 5.5 | after step 30            | 23             | 0.0051        | 9.53             | 12          |
|            | 4     | Sonnet 5.5 | all at once from step 0  | 13             | 0.0051        | 10.60            | 32          |
|            | 4     | Sonnet 5.5 | all at once from step 15 | 16             | 0.0051        | 10.04            | 14          |

DeepSeek adapter, low thinking:

| Seed house | Chain | Model                 | House                    | Corridor rooms | Privacy order | Walking distance | Compactness |
| ---------- | ----- | --------------------- | ------------------------ | -------------- | ------------- | ---------------- | ----------- |
| 1          |       |                       | seed house (70 rooms)    | 42             | 0.0037        | 9.56             | 8           |
|            | 5     | DeepSeek adapter, low | after step 30            | 0              | 0.0051        | 11.38            | 22          |
|            | 5     | DeepSeek adapter, low | all at once from step 0  | 0              | 0.0077        | 11.34            | 0           |
|            | 5     | DeepSeek adapter, low | all at once from step 15 | 44             | 0.0026        | 14.91            | 26          |
| 3          |       |                       | seed house (70 rooms)    | 14             | 0.0074        | 7.96             | 16          |
|            | 7     | DeepSeek adapter, low | after step 30            | 0              | 0.0026        | 18.70            | 0           |
|            | 7     | DeepSeek adapter, low | all at once from step 0  | 0              | 0.0000        | 18.97            | 0           |
|            | 7     | DeepSeek adapter, low | all at once from step 15 | 19             | 0.0051        | 11.99            | 10          |

Before the run we expected the house after step 30 to score no worse than the house built all at once from step 0, as on
the small grid. In the Sonnet chains that held for walking distance, which was lower after step 30 in every seed house,
and for compactness in three of the four. It failed for corridor rooms, which was higher after step 30
in every seed house. The all-at-once agents from step 0 left corridor rooms exactly where the seed house had it in
three houses, and one higher in the other. Privacy order was the same in every 100-room house of a
seed house. The DeepSeek houses after step 30 and built all at once from step 0 had corridor rooms 0 in both houses. The
scores of every step are in Appendix A.

### 3.2 What the agents changed

| Model                 | Agent              | Calls | Calls that removed a room | Most rooms removed by one call | Least share of the house kept | Hallways added per call |
| --------------------- | ------------------ | ----- | ------------------------- | ------------------------------ | ----------------------------- | ----------------------- |
| Sonnet 5.5            | One room at a time | 120   | 35                        | 1                              | 98.7%                         | 0.33                    |
| Sonnet 5.5            | All at once        | 116   | 78                        | 3                              | 97.5%                         | 10.47                   |
| DeepSeek adapter, low | One room at a time | 60    | 34                        | 115                            | 25.5%                         | 2.40                    |
| DeepSeek adapter, low | All at once        | 58    | 41                        | 110                            | 23.7%                         | 24.64                   |

No Sonnet agent refactored the house. A one-room step removed at most one room, and an all-at-once call kept at least
97.5% of the house it received. The difference between the two kinds of agent was in what they added: a
one-room step added 0.33 hallways on average, an all-at-once call 10.47.

DeepSeek refactored, mostly when it saw all the rooms at once. Its one-room steps removed rooms in
34 of 60 calls, but only one step in each house removed 10% or more of the house,
up to 75%. Its all-at-once calls removed 10% or more in 8 and 7 of the 29 calls in each house,
among them the first call in each house (68% and 75% of the house). A one-room step added 2.40
hallways on average, an all-at-once call 24.64.

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

| Model                 | Agent              | Tries | Valid | Script rejected | House invalid | Reply cut off | Output tokens per try | Cost per try |
| --------------------- | ------------------ | ----- | ----- | --------------- | ------------- | ------------- | --------------------- | ------------ |
| Sonnet 5.5            | One room at a time | 129   | 120   | 7               | 2             | 0             | 925                   | $0.025       |
| Sonnet 5.5            | All at once        | 123   | 116   | 2               | 5             | 0             | 2661                  | $0.043       |
| DeepSeek adapter, low | One room at a time | 62    | 60    | 0               | 2             | 0             | 6942                  | $0.004       |
| DeepSeek adapter, low | All at once        | 62    | 58    | 0               | 4             | 0             | 15605                 | $0.010       |

Every failed call was tried again with a fresh agent and succeeded within three tries; every chain has all 59 houses.
The Sonnet cost is the Claude Code figure; the DeepSeek cost is computed from DeepSeek's published prices.

## 4. Run 2: no hallway can be built

### 4.1 The houses at the end

Sonnet 5.5:

| Seed house | Chain | Model      | House                    | Corridor rooms | Privacy order | Walking distance | Compactness |
| ---------- | ----- | ---------- | ------------------------ | -------------- | ------------- | ---------------- | ----------- |
| 1          |       |            | seed house (70 rooms)    | 42             | 0.0037        | 9.56             | 8           |
|            | 1     | Sonnet 5.5 | after step 30            | 63             | 0.0026        | 11.89            | 12          |
|            | 1     | Sonnet 5.5 | all at once from step 0  | 64             | 0.0026        | 11.69            | 10          |
|            | 1     | Sonnet 5.5 | all at once from step 15 | 65             | 0.0026        | 11.92            | 10          |
|            | 9     | Sonnet 5.5 | after step 30            | 62             | 0.0026        | 12.00            | 12          |
|            | 9     | Sonnet 5.5 | all at once from step 0  | 67             | 0.0026        | 11.69            | 10          |
|            | 9     | Sonnet 5.5 | all at once from step 15 | 64             | 0.0026        | 12.22            | 14          |
| 2          |       |            | seed house (70 rooms)    | 42             | 0.0037        | 9.91             | 12          |
|            | 2     | Sonnet 5.5 | after step 30            | 65             | 0.0026        | 12.61            | 18          |
|            | 2     | Sonnet 5.5 | all at once from step 0  | 65             | 0.0026        | 13.13            | 26          |
|            | 2     | Sonnet 5.5 | all at once from step 15 | 67             | 0.0026        | 12.43            | 14          |
|            | 10    | Sonnet 5.5 | after step 30            | 67             | 0.0026        | 12.51            | 14          |
|            | 10    | Sonnet 5.5 | all at once from step 0  | 66             | 0.0026        | 12.05            | 8           |
|            | 10    | Sonnet 5.5 | all at once from step 15 | 67             | 0.0026        | 12.15            | 8           |
| 3          |       |            | seed house (70 rooms)    | 14             | 0.0074        | 7.96             | 16          |
|            | 3     | Sonnet 5.5 | after step 30            | 45             | 0.0051        | 9.04             | 8           |
|            | 3     | Sonnet 5.5 | all at once from step 0  | 31             | 0.0051        | 10.65            | 18          |
|            | 3     | Sonnet 5.5 | all at once from step 15 | 46             | 0.0051        | 9.06             | 8           |
|            | 11    | Sonnet 5.5 | after step 30            | 37             | 0.0051        | 8.95             | 2           |
|            | 11    | Sonnet 5.5 | all at once from step 0  | 40             | 0.0051        | 8.99             | 18          |
|            | 11    | Sonnet 5.5 | all at once from step 15 | 40             | 0.0051        | 8.98             | 10          |
| 4          |       |            | seed house (70 rooms)    | 13             | 0.0074        | 7.60             | 8           |
|            | 4     | Sonnet 5.5 | after step 30            | 38             | 0.0051        | 8.65             | 0           |
|            | 4     | Sonnet 5.5 | all at once from step 0  | 43             | 0.0051        | 8.72             | 8           |
|            | 4     | Sonnet 5.5 | all at once from step 15 | 39             | 0.0051        | 8.65             | 0           |
|            | 12    | Sonnet 5.5 | after step 30            | 44             | 0.0051        | 8.84             | 4           |
|            | 12    | Sonnet 5.5 | all at once from step 0  | 43             | 0.0051        | 8.72             | 8           |
|            | 12    | Sonnet 5.5 | all at once from step 15 | 37             | 0.0051        | 8.73             | 2           |

GPT-6 Luna:

| Seed house | Chain | Model      | House                    | Corridor rooms | Privacy order | Walking distance | Compactness |
| ---------- | ----- | ---------- | ------------------------ | -------------- | ------------- | ---------------- | ----------- |
| 1          |       |            | seed house (70 rooms)    | 42             | 0.0037        | 9.56             | 8           |
|            | 5     | GPT-6 Luna | after step 30            | 86             | 0.0026        | 8.08             | 10          |
|            | 5     | GPT-6 Luna | all at once from step 0  | 79             | 0.0026        | 9.82             | 8           |
|            | 5     | GPT-6 Luna | all at once from step 15 | 83             | 0.0026        | 7.76             | 8           |
| 2          |       |            | seed house (70 rooms)    | 42             | 0.0037        | 9.91             | 12          |
|            | 6     | GPT-6 Luna | after step 30            | 93             | 0.0026        | 8.13             | 6           |
|            | 6     | GPT-6 Luna | all at once from step 0  | 75             | 0.0026        | 12.31            | 24          |
|            | 6     | GPT-6 Luna | all at once from step 15 | 91             | 0.0026        | 7.79             | 0           |
| 3          |       |            | seed house (70 rooms)    | 14             | 0.0074        | 7.96             | 16          |
|            | 7     | GPT-6 Luna | after step 30            | 48             | 0.0051        | 10.87            | 10          |
|            | 7     | GPT-6 Luna | all at once from step 0  | 43             | 0.0051        | 13.84            | 18          |
|            | 7     | GPT-6 Luna | all at once from step 15 | 45             | 0.0051        | 9.85             | 10          |
| 4          |       |            | seed house (70 rooms)    | 13             | 0.0074        | 7.60             | 8           |
|            | 8     | GPT-6 Luna | after step 30            | 49             | 0.0051        | 10.06            | 22          |
|            | 8     | GPT-6 Luna | all at once from step 0  | 34             | 0.0051        | 9.78             | 14          |
|            | 8     | GPT-6 Luna | all at once from step 15 | 50             | 0.0051        | 10.44            | 16          |

One call has no valid house: the all-at-once call from step 5 in house 2, chain 6 (GPT-6 Luna), whose three tries were all rejected; the chain went on without it. The
scores of every step are in Appendix B.

Across the eight Sonnet chains, the house after step 30 had fewer corridor rooms than the house built all at
once from step 0 in four chains and more in three; it was shorter to walk in
four and longer in four. Across the four GPT-6 Luna chains, the house after
step 30 had more corridor rooms in all four; it was shorter to walk in
three and longer in one.

Every chain of both models ended with more corridor rooms than its seed house had, and GPT-6 Luna ended with more than
both Sonnet chains in every seed house. In the two budget houses GPT-6 Luna's houses were shorter to walk than
Sonnet's; in the two planned houses they were longer.

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
step 6 of house 1, chain 5 (GPT-6 Luna), which added 57 doors and raised corridor rooms from 47 to
70. And six calls removed a quarter of the house or more, one
of them a one-room step, all in the budget houses. In each budget house one one-room step, step
6, redesigned the house, and the later steps built on that design. Every call that rewired or
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

| Model      | Agent              | Tries | Valid | Script rejected | House invalid | Reply cut off | Output tokens per try | Cost per try |
| ---------- | ------------------ | ----- | ----- | --------------- | ------------- | ------------- | --------------------- | ------------ |
| Sonnet 5.5 | One room at a time | 246   | 240   | 4               | 2             | 0             | 804                   | $0.024       |
| Sonnet 5.5 | All at once        | 235   | 232   | 1               | 2             | 0             | 1703                  | $0.034       |
| GPT-6 Luna | One room at a time | 134   | 120   | 7               | 7             | 0             | not reported          | not reported |
| GPT-6 Luna | All at once        | 143   | 115   | 19              | 5             | 4             | not reported          | not reported |

Copilot CLI does not report tokens or cost for GPT-6 Luna.

## 5. Run 3: reorganise first

### 5.1 The houses at the end

Sonnet 5.5:

| Seed house | Chain | Model      | House                    | Corridor rooms | Privacy order | Walking distance | Compactness |
| ---------- | ----- | ---------- | ------------------------ | -------------- | ------------- | ---------------- | ----------- |
| 1          |       |            | seed house (70 rooms)    | 42             | 0.0037        | 9.56             | 8           |
|            | 1     | Sonnet 5.5 | after step 30            | 1              | 0.0000        | 11.11            | 16          |
|            | 1     | Sonnet 5.5 | all at once from step 0  | 0              | 0.0000        | 16.53            | 2           |
|            | 1     | Sonnet 5.5 | all at once from step 15 | 0              | 0.0000        | 11.69            | 34          |
| 2          |       |            | seed house (70 rooms)    | 42             | 0.0037        | 9.91             | 12          |
|            | 2     | Sonnet 5.5 | after step 30            | 0              | 0.0000        | 11.42            | 0           |
|            | 2     | Sonnet 5.5 | all at once from step 0  | 0              | 0.0000        | 16.53            | 2           |
|            | 2     | Sonnet 5.5 | all at once from step 15 | 0              | 0.0000        | 11.53            | 4           |
| 3          |       |            | seed house (70 rooms)    | 14             | 0.0074        | 7.96             | 16          |
|            | 3     | Sonnet 5.5 | after step 30            | 0              | 0.0026        | 11.02            | 0           |
|            | 3     | Sonnet 5.5 | all at once from step 0  | 0              | 0.0000        | 11.14            | 0           |
|            | 3     | Sonnet 5.5 | all at once from step 15 | 0              | 0.0026        | 10.96            | 10          |
| 4          |       |            | seed house (70 rooms)    | 13             | 0.0074        | 7.60             | 8           |
|            | 4     | Sonnet 5.5 | after step 30            | 0              | 0.0000        | 11.27            | 0           |
|            | 4     | Sonnet 5.5 | all at once from step 0  | 0              | 0.0077        | 11.65            | 2           |
|            | 4     | Sonnet 5.5 | all at once from step 15 | 0              | 0.0077        | 11.72            | 2           |

DeepSeek adapter, low thinking:

| Seed house | Chain | Model                 | House                    | Corridor rooms | Privacy order | Walking distance | Compactness |
| ---------- | ----- | --------------------- | ------------------------ | -------------- | ------------- | ---------------- | ----------- |
| 1          |       |                       | seed house (70 rooms)    | 42             | 0.0037        | 9.56             | 8           |
|            | 5     | DeepSeek adapter, low | after step 30            | 0              | 0.0077        | 14.88            | 0           |
|            | 5     | DeepSeek adapter, low | all at once from step 0  | 42             | 0.0026        | 15.06            | 28          |
|            | 5     | DeepSeek adapter, low | all at once from step 15 | 0              | 0.0000        | 18.63            | 0           |
| 3          |       |                       | seed house (70 rooms)    | 14             | 0.0074        | 7.96             | 16          |
|            | 7     | DeepSeek adapter, low | after step 30            | 0              | 0.0026        | 17.59            | 0           |
|            | 7     | DeepSeek adapter, low | all at once from step 0  | 0              | 0.0000        | 14.18            | 0           |
|            | 7     | DeepSeek adapter, low | all at once from step 15 | 0              | 0.0000        | 13.04            | 0           |

One call has no valid house: the all-at-once call from step 2 in house 1, chain 5 (DeepSeek adapter, low), whose three tries were all rejected; the chain went on without it. The
scores of every step are in Appendix C.

Before the run we expected the house after step 30 to score no worse than the house built all at once from step 0,
as in the free 5×5 runs. The scores no longer settled it: corridor rooms were the same in four of the six chains,
lower after step 30 in one and higher in one; walking distance was lower after step 30 in
five chains and higher in one. The difference that mattered was not in the scores: the
agents now rebuilt the house.

The instruction changed what the agents did. The first one-room steps removed most of the seed house and rebuilt it,
and the final houses after step 30 had corridor rooms 0 in five of the six. One all-at-once call from
the seed did not rebuild: the agent kept the seed house and added a wing, and the house kept the seed's corridor
rooms; the other houses built all at once from step 0 had corridor rooms 0 in five of the six. Once both
kinds of agent rebuilt, the corridor score no longer separated one room at a time from all at once; the difference
that remained was a walk, not a passage.

### 5.2 What the agents changed

| Model                 | Agent              | Calls | Calls that removed a room | Most rooms removed by one call | Least share of the house kept | Hallways added per call |
| --------------------- | ------------------ | ----- | ------------------------- | ------------------------------ | ----------------------------- | ----------------------- |
| Sonnet 5.5            | One room at a time | 120   | 51                        | 122                            | 18.7%                         | 1.17                    |
| Sonnet 5.5            | All at once        | 116   | 73                        | 107                            | 26.2%                         | 11.65                   |
| DeepSeek adapter, low | One room at a time | 60    | 58                        | 195                            | 5.2%                          | 1.77                    |
| DeepSeek adapter, low | All at once        | 57    | 53                        | 190                            | 5.6%                          | 13.88                   |

The Sonnet one-room steps removed rooms in 51 of 120 calls, up to 122
in one, and kept as little as 18.7% of the house; the all-at-once calls removed rooms in
73 of 116, up to 107, and kept as little as 26.2%. The
DeepSeek chains removed more: the one-room steps removed rooms in 58 of 60 calls,
up to 195, and kept as little as 5.2%; the all-at-once calls removed rooms in
53 of 57, up to 190, and kept as little as 5.6%. A
one-room step added 1.17 hallways on average in the Sonnet chains and 1.77 in the DeepSeek
ones; an all-at-once call added 11.65 and 13.88.

### 5.3 Why it happens

The reorganise sentence asked every agent to reduce the complexity of the house before adding to it. The Sonnet
agents did: the first one-room steps removed 49, 56, 72 and 13 rooms in the four chains, and the all-at-once calls
removed rooms too. The DeepSeek adapter at low thinking removed more overall: its first steps removed 53 and 77
rooms, and across its one-room steps it kept as little as 5.2% of the house against the Sonnet
18.7%. The houses that were rebuilt the most were not the shortest to walk: the DeepSeek one-room steps kept less of the
house than the Sonnet ones, and the DeepSeek houses were longer to walk. The all-at-once call from the seed in one
DeepSeek chain kept the seed house and added a wing rather than rebuilding; the one-room step that followed rebuilt
it. The instruction is the lever; where it failed, it failed at the individual call. Redesigning was not the same as
improving.

### 5.4 Failed calls and cost

| Model                 | Agent              | Tries | Valid | Script rejected | House invalid | Reply cut off | Output tokens per try | Cost per try |
| --------------------- | ------------------ | ----- | ----- | --------------- | ------------- | ------------- | --------------------- | ------------ |
| Sonnet 5.5            | One room at a time | 122   | 120   | 1               | 1             | 0             | 2560                  | $0.044       |
| Sonnet 5.5            | All at once        | 119   | 116   | 1               | 2             | 0             | 4246                  | $0.060       |
| DeepSeek adapter, low | One room at a time | 66    | 60    | 4               | 2             | 0             | 20007                 | $0.012       |
| DeepSeek adapter, low | All at once        | 70    | 57    | 8               | 5             | 0             | 20849                 | $0.013       |

The Sonnet cost is the Claude Code figure; the DeepSeek cost is computed from DeepSeek's published prices. Run 3 is
a free world: building and demolishing cost nothing.

## 6. Run 4: reorganise, with cost

### 6.1 The houses at the end

Sonnet 5.5:

| Seed house | Chain | Model      | House                    | Corridor rooms | Privacy order | Walking distance | Compactness |
| ---------- | ----- | ---------- | ------------------------ | -------------- | ------------- | ---------------- | ----------- |
| 1          |       |            | seed house (70 rooms)    | 42             | 0.0037        | 9.56             | 8           |
|            | 5     | Sonnet 5.5 | after step 30            | 65             | 0.0026        | 12.12            | 12          |
|            | 5     | Sonnet 5.5 | all at once from step 0  | 70             | 0.0026        | 11.70            | 2           |
|            | 5     | Sonnet 5.5 | all at once from step 15 | 57             | 0.0026        | 13.38            | 22          |
| 2          |       |            | seed house (70 rooms)    | 42             | 0.0037        | 9.91             | 12          |
|            | 6     | Sonnet 5.5 | after step 30            | 64             | 0.0026        | 12.49            | 18          |
|            | 6     | Sonnet 5.5 | all at once from step 0  | 43             | 0.0026        | 14.58            | 30          |
|            | 6     | Sonnet 5.5 | all at once from step 15 | 54             | 0.0026        | 13.77            | 24          |
| 3          |       |            | seed house (70 rooms)    | 14             | 0.0074        | 7.96             | 16          |
|            | 7     | Sonnet 5.5 | after step 30            | 38             | 0.0051        | 8.95             | 8           |
|            | 7     | Sonnet 5.5 | all at once from step 0  | 12             | 0.0051        | 14.93            | 12          |
|            | 7     | Sonnet 5.5 | all at once from step 15 | 29             | 0.0051        | 10.81            | 10          |
| 4          |       |            | seed house (70 rooms)    | 13             | 0.0074        | 7.60             | 8           |
|            | 8     | Sonnet 5.5 | after step 30            | 34             | 0.0051        | 8.75             | 6           |
|            | 8     | Sonnet 5.5 | all at once from step 0  | 13             | 0.0051        | 10.53            | 30          |
|            | 8     | Sonnet 5.5 | all at once from step 15 | 24             | 0.0051        | 10.53            | 22          |

DeepSeek adapter, low thinking:

| Seed house | Chain | Model                 | House                    | Corridor rooms | Privacy order | Walking distance | Compactness |
| ---------- | ----- | --------------------- | ------------------------ | -------------- | ------------- | ---------------- | ----------- |
| 1          |       |                       | seed house (70 rooms)    | 42             | 0.0037        | 9.56             | 8           |
|            | 1     | DeepSeek adapter, low | after step 30            | 0              | 0.0077        | 17.02            | 58          |
|            | 1     | DeepSeek adapter, low | all at once from step 0  | 0              | 0.0077        | 11.73            | 0           |
|            | 1     | DeepSeek adapter, low | all at once from step 15 | 0              | 0.0000        | 12.01            | 0           |
| 3          |       |                       | seed house (70 rooms)    | 14             | 0.0074        | 7.96             | 16          |
|            | 3     | DeepSeek adapter, low | after step 30            | 0              | 0.0102        | 12.87            | 12          |
|            | 3     | DeepSeek adapter, low | all at once from step 0  | 0              | 0.0077        | 12.20            | 0           |
|            | 3     | DeepSeek adapter, low | all at once from step 15 | 0              | 0.0000        | 17.59            | 0           |

The scores of every step are in Appendix D.

In the Sonnet chains the house after step 30 had more corridor rooms than the house built all at once from step 0 in
three of the four houses and fewer in one; it was shorter to walk in
three and longer in one. The DeepSeek houses after step 30 and built all at once from
step 0 had corridor rooms 0 in both houses, and the houses after step 30 were longer to walk.

### 6.2 What the agents changed

| Model                 | Agent              | Calls | Calls that removed a room | Most rooms removed by one call | Least share of the house kept | Hallways added per call |
| --------------------- | ------------------ | ----- | ------------------------- | ------------------------------ | ----------------------------- | ----------------------- |
| Sonnet 5.5            | One room at a time | 120   | 1                         | 1                              | 99.2%                         | 0.01                    |
| Sonnet 5.5            | All at once        | 116   | 35                        | 2                              | 97.8%                         | 6.91                    |
| DeepSeek adapter, low | One room at a time | 60    | 44                        | 116                            | 16.5%                         | 1.13                    |
| DeepSeek adapter, low | All at once        | 58    | 42                        | 125                            | 5.3%                          | 16.19                   |

With cost, Sonnet did not refactor, although every agent was asked to reorganise. Its one-room steps removed a room in
one of 120 calls, its all-at-once calls in 35 of
116, and no call removed more than 2.2% of the house it received; in run 3, without cost, a
single call removed up to 81%.

DeepSeek still refactored. Its first one-room step removed 80% and 50% of the house, and one call up to
95%. Its one-room steps removed 10% or more of the house in 10 and 13 of the 30 steps in each house,
against 23 and 25 in run 3; its all-at-once calls in 11 and 16 of 29.

### 6.3 Why it happens

The prompt asks for two things: reorganise the house, and keep the total cost of the script low. Refactoring means
removing rooms and building them again, and every one of those commands has a price. Sonnet chose cost: the median
Sonnet one-room script cost 5, the new room and one door, and none cost more than
20. It acted locally, as in run 1, where nobody asked it to reorganise. DeepSeek chose to
reorganise: its median one-room script cost 29.5, and one cost 1694. The cost
constrained it, in fewer calls than in run 3, but did not stop it.

### 6.4 Failed calls and cost

| Model                 | Agent              | Tries | Valid | Script rejected | House invalid | Reply cut off | Output tokens per try | Cost per try |
| --------------------- | ------------------ | ----- | ----- | --------------- | ------------- | ------------- | --------------------- | ------------ |
| Sonnet 5.5            | One room at a time | 122   | 120   | 2               | 0             | 0             | 856                   | $0.026       |
| Sonnet 5.5            | All at once        | 117   | 116   | 0               | 1             | 0             | 2845                  | $0.046       |
| DeepSeek adapter, low | One room at a time | 63    | 60    | 2               | 1             | 0             | 18459                 | $0.011       |
| DeepSeek adapter, low | All at once        | 63    | 58    | 0               | 5             | 0             | 19628                 | $0.012       |

The Sonnet cost is the Claude Code figure; the DeepSeek cost is computed from DeepSeek's published prices.

## 7. Run 5: cost, no reorganise

### 7.1 The houses at the end

Sonnet 5.5:

| Seed house | Chain | Model      | House                    | Corridor rooms | Privacy order | Walking distance | Compactness |
| ---------- | ----- | ---------- | ------------------------ | -------------- | ------------- | ---------------- | ----------- |
| 1          |       |            | seed house (70 rooms)    | 42             | 0.0037        | 9.56             | 8           |
|            | 5     | Sonnet 5.5 | after step 30            | 67             | 0.0026        | 11.58            | 10          |
|            | 5     | Sonnet 5.5 | all at once from step 0  | 67             | 0.0026        | 11.46            | 6           |
|            | 5     | Sonnet 5.5 | all at once from step 15 | 66             | 0.0026        | 11.78            | 10          |
| 3          |       |            | seed house (70 rooms)    | 14             | 0.0074        | 7.96             | 16          |
|            | 7     | Sonnet 5.5 | after step 30            | 38             | 0.0051        | 8.92             | 2           |
|            | 7     | Sonnet 5.5 | all at once from step 0  | 40             | 0.0051        | 8.95             | 18          |
|            | 7     | Sonnet 5.5 | all at once from step 15 | 41             | 0.0051        | 8.86             | 16          |

DeepSeek adapter, low thinking:

| Seed house | Chain | Model                 | House                    | Corridor rooms | Privacy order | Walking distance | Compactness |
| ---------- | ----- | --------------------- | ------------------------ | -------------- | ------------- | ---------------- | ----------- |
| 1          |       |                       | seed house (70 rooms)    | 42             | 0.0037        | 9.56             | 8           |
|            | 1     | DeepSeek adapter, low | after step 30            | 51             | 0.0026        | 12.92            | 14          |
|            | 1     | DeepSeek adapter, low | all at once from step 0  | 63             | 0.0026        | 13.32            | 24          |
|            | 1     | DeepSeek adapter, low | all at once from step 15 | 65             | 0.0026        | 14.13            | 34          |
| 3          |       |                       | seed house (70 rooms)    | 14             | 0.0074        | 7.96             | 16          |
|            | 3     | DeepSeek adapter, low | after step 30            | 40             | 0.0051        | 11.53            | 10          |
|            | 3     | DeepSeek adapter, low | all at once from step 0  | 14             | 0.0051        | 12.84            | 40          |
|            | 3     | DeepSeek adapter, low | all at once from step 15 | 28             | 0.0051        | 12.93            | 16          |

The scores of every step are in Appendix E.

On the small grid, with hallways, cost and no request to reorganise, houses built step by step ended worse than
planned ones. Run 5 has the same conditions at 100 rooms. In the Sonnet chains the house after step 30 and the house
built all at once from step 0 ended with corridor rooms 67 against 67 in house 1 and 38 against 40 in house 3, and with walking distances within 0.15 of
each other. In the DeepSeek chains the house after step 30 had fewer corridor rooms in house 1 and more in house 3.

### 7.2 What the agents changed

| Model                 | Agent              | Calls | Calls that removed a room | Most rooms removed by one call | Least share of the house kept | Hallways added per call |
| --------------------- | ------------------ | ----- | ------------------------- | ------------------------------ | ----------------------------- | ----------------------- |
| Sonnet 5.5            | One room at a time | 60    | 0                         | 0                              | 100.0%                        | 0.00                    |
| Sonnet 5.5            | All at once        | 58    | 2                         | 1                              | 99.2%                         | 3.05                    |
| DeepSeek adapter, low | One room at a time | 60    | 31                        | 1                              | 98.7%                         | 0.32                    |
| DeepSeek adapter, low | All at once        | 58    | 32                        | 1                              | 98.8%                         | 6.33                    |

Neither model refactored. No Sonnet one-room step removed a room, and two of its
58 all-at-once calls removed one each. No DeepSeek call removed more than one room.

### 7.3 Why it happens

Every Sonnet one-room script cost 5: the new room and one door into a room already there, the cheapest valid answer,
as on the small grid. What differed from the small grid is the all-at-once agent. In run 1, without cost, it hung a
hallway wing behind the house and added 10.47 hallways per call; with cost it added 3.05, and
its houses gained corridor rooms, from 42 to 67 in house 1 and from 14 to 40 in house 3. Both kinds of agent acted locally, so neither kind of house
came out ahead.

### 7.4 Failed calls and cost

| Model                 | Agent              | Tries | Valid | Script rejected | House invalid | Reply cut off | Output tokens per try | Cost per try |
| --------------------- | ------------------ | ----- | ----- | --------------- | ------------- | ------------- | --------------------- | ------------ |
| Sonnet 5.5            | One room at a time | 60    | 60    | 0               | 0             | 0             | 733                   | $0.024       |
| Sonnet 5.5            | All at once        | 58    | 58    | 0               | 0             | 0             | 1800                  | $0.035       |
| DeepSeek adapter, low | One room at a time | 60    | 60    | 0               | 0             | 0             | 8704                  | $0.005       |
| DeepSeek adapter, low | All at once        | 60    | 58    | 0               | 2             | 0             | 13127                 | $0.008       |

The Sonnet cost is the Claude Code figure; the DeepSeek cost is computed from DeepSeek's published prices.

## 8. Limitations

Each run has one chain per seed house and model, except Sonnet in run 2, which has two. The DeepSeek chains cover
only houses 1 and 3, and so do the Sonnet chains in run 5. Each model ran at one effort level, and GPT-6 Luna in one
run. The DeepSeek chains use a standalone adapter with a clean prompt and low thinking, not Claude Code; they are not
comparable with the Sonnet chains point by point. DeepSeek is many times slower than Sonnet, a mean of
92 seconds per call against 18, and a mean of 1.6 hours per chain against
0.3; and it was run at low thinking because at high effort it was even slower. Claude Code changed version between the runs and within run 2
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
advantage of using an incremental or an all-at-once strategy in terms of the final design quality. <u>When asked to
reorganise, DeepSeek's successive layouts are far more distinct from each other than Sonnet's, which stays close to
the layout it received.</u>
- Run 1 (no cost, no reorganise): 1 of 30 steps in each house refactored 10% or more of the house, against 8 and 7
  of 29 all-at-once calls. The first all-at-once call refactored 68% and 75%.
- Run 3 (no cost, reorganise): 23 and 25 of 30 steps refactored 10% or more. In house 1 the first step used 297
  commands to add one bedroom.
- Run 4 (cost, reorganise): 10 and 13 of 30 steps refactored 10% or more.
- Run 5 (cost, no reorganise): no call refactored 10% or more.

3. Opus 5.5 (medium effort). By default it works much as it does under cost and reorganise: it refactors once at the
start, then keeps what it built and adds the new rooms on top. Only cost without a request to reorganise stops that first
refactoring, and in that case the incremental house ended with more corridor rooms than the all-at-once houses. On house 1
neither Sonnet nor DeepSeek did this.
- Run 1 (no cost, no reorganise), houses 1 and 2: the first step refactored 65% and 77% of the house, and the first
  all-at-once call 67% and 67%. No later call refactored 10% or more. All its final houses have 0 or 1 corridor rooms.
- Run 4 (cost, reorganise), house 1: the first step refactored 39% and the first all-at-once call 36%. No later call
  refactored 10% or more. All its final houses have 0 corridor rooms.
- Run 5 (cost, no reorganise), house 1: no call refactored more than 2.4%. The incremental house ended with 65 corridor
  rooms against 41 and 53 for the all-at-once houses.

4. The 5×5 result. On the 5×5 grid, with hallways, cost and no reorganise, houses built step by step ended worse than
planned ones. Run 5 has the same conditions at 100 rooms, and with Sonnet the two houses showed no difference. There
is no evidence supporting an advantage in working step by step other than the one collected during the 5×5
experiment.

## Appendix A. Run 1, step by step

Each row is one kind of house in one chain: the house after the step, or the house built all at once from the house
after that step. Step 0 of "after the step" is the seed house. All-at-once calls start from steps 0 to 28, so step 30
has none.

**Corridor rooms**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5            | after the step            | 42     | 43     | 44      | 47      | 50      | 54      | 59      |
| 1     | 1          | Sonnet 5.5            | all at once from the step | 42     | 42     | 45      | 48      | 51      | 54      | –       |
| 2     | 2          | Sonnet 5.5            | after the step            | 42     | 44     | 48      | 51      | 54      | 57      | 57      |
| 2     | 2          | Sonnet 5.5            | all at once from the step | 42     | 45     | 48      | 51      | 55      | 62      | –       |
| 3     | 3          | Sonnet 5.5            | after the step            | 14     | 15     | 15      | 17      | 20      | 21      | 21      |
| 3     | 3          | Sonnet 5.5            | all at once from the step | 15     | 15     | 15      | 17      | 20      | 21      | –       |
| 4     | 4          | Sonnet 5.5            | after the step            | 13     | 13     | 14      | 16      | 17      | 19      | 23      |
| 4     | 4          | Sonnet 5.5            | all at once from the step | 13     | 13     | 14      | 16      | 17      | 19      | –       |
| 9     | 1          | Opus 5.5              | after the step            | 42     | 0      | 0       | 0       | 0       | 0       | 0       |
| 9     | 1          | Opus 5.5              | all at once from the step | 0      | 0      | 0       | 0       | 0       | 0       | –       |
| 10    | 2          | Opus 5.5              | after the step            | 42     | 0      | 0       | 0       | 1       | 1       | 1       |
| 10    | 2          | Opus 5.5              | all at once from the step | 0      | 0      | 0       | 0       | 1       | 1       | –       |
| 5     | 1          | DeepSeek adapter, low | after the step            | 42     | 42     | 43      | 44      | 0       | 0       | 0       |
| 5     | 1          | DeepSeek adapter, low | all at once from the step | 0      | 0      | 0       | 44      | 0       | 0       | –       |
| 7     | 3          | DeepSeek adapter, low | after the step            | 14     | 15     | 15      | 19      | 19      | 0       | 0       |
| 7     | 3          | DeepSeek adapter, low | all at once from the step | 0      | 15     | 15      | 19      | 19      | 0       | –       |

**Privacy order**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5            | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 1     | 1          | Sonnet 5.5            | all at once from the step | 0.0026 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 2     | 2          | Sonnet 5.5            | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 2     | 2          | Sonnet 5.5            | all at once from the step | 0.0026 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 3     | 3          | Sonnet 5.5            | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0054  | 0.0051  |
| 3     | 3          | Sonnet 5.5            | all at once from the step | 0.0051 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0051  | –       |
| 4     | 4          | Sonnet 5.5            | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0054  | 0.0051  |
| 4     | 4          | Sonnet 5.5            | all at once from the step | 0.0051 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0051  | –       |
| 9     | 1          | Opus 5.5              | after the step            | 0.0037 | 0.0000 | 0.0000  | 0.0000  | 0.0000  | 0.0000  | 0.0000  |
| 9     | 1          | Opus 5.5              | all at once from the step | 0.0026 | 0.0000 | 0.0000  | 0.0000  | 0.0000  | 0.0000  | –       |
| 10    | 2          | Opus 5.5              | after the step            | 0.0037 | 0.0000 | 0.0000  | 0.0000  | 0.0000  | 0.0000  | 0.0000  |
| 10    | 2          | Opus 5.5              | all at once from the step | 0.0000 | 0.0000 | 0.0000  | 0.0000  | 0.0000  | 0.0000  | –       |
| 5     | 1          | DeepSeek adapter, low | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0000  | 0.0054  | 0.0051  |
| 5     | 1          | DeepSeek adapter, low | all at once from the step | 0.0077 | 0.0000 | 0.0000  | 0.0026  | 0.0000  | 0.0051  | –       |
| 7     | 3          | DeepSeek adapter, low | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0000  | 0.0026  |
| 7     | 3          | DeepSeek adapter, low | all at once from the step | 0.0000 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0000  | –       |

**Walking distance**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5            | after the step            | 9.56   | 9.91   | 10.36   | 10.67   | 10.87   | 11.17   | 11.43   |
| 1     | 1          | Sonnet 5.5            | all at once from the step | 15.22  | 13.22  | 12.13   | 13.68   | 12.85   | 11.48   | –       |
| 2     | 2          | Sonnet 5.5            | after the step            | 9.91   | 10.36  | 10.94   | 11.38   | 11.77   | 12.24   | 12.66   |
| 2     | 2          | Sonnet 5.5            | all at once from the step | 14.91  | 15.37  | 14.15   | 13.23   | 13.09   | 12.62   | –       |
| 3     | 3          | Sonnet 5.5            | after the step            | 7.96   | 8.24   | 8.80    | 9.18    | 9.56    | 10.01   | 10.40   |
| 3     | 3          | Sonnet 5.5            | all at once from the step | 14.47  | 11.32  | 13.71   | 11.37   | 10.42   | 10.61   | –       |
| 4     | 4          | Sonnet 5.5            | after the step            | 7.60   | 8.01   | 8.29    | 8.67    | 8.97    | 9.35    | 9.53    |
| 4     | 4          | Sonnet 5.5            | all at once from the step | 10.60  | 10.71  | 10.13   | 10.04   | 9.78    | 9.82    | –       |
| 9     | 1          | Opus 5.5              | after the step            | 9.56   | 9.80   | 10.13   | 10.61   | 10.72   | 10.91   | 11.13   |
| 9     | 1          | Opus 5.5              | all at once from the step | 14.77  | 11.08  | 11.05   | 11.48   | 11.48   | 11.13   | –       |
| 10    | 2          | Opus 5.5              | after the step            | 9.91   | 9.80   | 10.16   | 10.69   | 10.72   | 10.92   | 11.14   |
| 10    | 2          | Opus 5.5              | all at once from the step | 11.14  | 11.14  | 11.20   | 11.71   | 11.43   | 11.30   | –       |
| 5     | 1          | DeepSeek adapter, low | after the step            | 9.56   | 10.35  | 11.05   | 11.97   | 11.21   | 11.31   | 11.38   |
| 5     | 1          | DeepSeek adapter, low | all at once from the step | 11.34  | 18.74  | 11.70   | 14.91   | 11.49   | 11.43   | –       |
| 7     | 3          | DeepSeek adapter, low | after the step            | 7.96   | 8.46   | 9.00    | 9.36    | 9.62    | 15.00   | 18.70   |
| 7     | 3          | DeepSeek adapter, low | all at once from the step | 18.97  | 12.92  | 12.30   | 11.99   | 10.87   | 16.48   | –       |

**Compactness**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5            | after the step            | 8      | 10     | 14      | 14      | 16      | 14      | 14      |
| 1     | 1          | Sonnet 5.5            | all at once from the step | 28     | 28     | 24      | 26      | 24      | 18      | –       |
| 2     | 2          | Sonnet 5.5            | after the step            | 12     | 10     | 12      | 14      | 20      | 20      | 20      |
| 2     | 2          | Sonnet 5.5            | all at once from the step | 34     | 28     | 28      | 22      | 30      | 20      | –       |
| 3     | 3          | Sonnet 5.5            | after the step            | 16     | 16     | 20      | 24      | 24      | 26      | 28      |
| 3     | 3          | Sonnet 5.5            | all at once from the step | 16     | 28     | 38      | 18      | 20      | 24      | –       |
| 4     | 4          | Sonnet 5.5            | after the step            | 8      | 6      | 10      | 10      | 8       | 14      | 12      |
| 4     | 4          | Sonnet 5.5            | all at once from the step | 32     | 34     | 26      | 14      | 14      | 14      | –       |
| 9     | 1          | Opus 5.5              | after the step            | 8      | 2      | 6       | 2       | 6       | 8       | 8       |
| 9     | 1          | Opus 5.5              | all at once from the step | 0      | 2      | 6       | 0       | 0       | 8       | –       |
| 10    | 2          | Opus 5.5              | after the step            | 12     | 2      | 4       | 2       | 6       | 10      | 8       |
| 10    | 2          | Opus 5.5              | all at once from the step | 0      | 2      | 4       | 4       | 0       | 12      | –       |
| 5     | 1          | DeepSeek adapter, low | after the step            | 8      | 14     | 16      | 16      | 26      | 28      | 22      |
| 5     | 1          | DeepSeek adapter, low | all at once from the step | 0      | 0      | 0       | 26      | 14      | 22      | –       |
| 7     | 3          | DeepSeek adapter, low | after the step            | 16     | 16     | 18      | 16      | 18      | 0       | 0       |
| 7     | 3          | DeepSeek adapter, low | all at once from the step | 0      | 20     | 14      | 10      | 28      | 0       | –       |

## Appendix B. Run 2, step by step

As in Appendix A.

**Corridor rooms**

| Chain | Seed house | Model      | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | ---------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5 | after the step            | 42     | 46     | 50      | 54      | 58      | 60      | 63      |
| 1     | 1          | Sonnet 5.5 | all at once from the step | 64     | 67     | 66      | 65      | 66      | 64      | –       |
| 2     | 2          | Sonnet 5.5 | after the step            | 42     | 46     | 50      | 54      | 57      | 61      | 65      |
| 2     | 2          | Sonnet 5.5 | all at once from the step | 65     | 68     | 66      | 67      | 64      | 66      | –       |
| 3     | 3          | Sonnet 5.5 | after the step            | 14     | 17     | 28      | 32      | 36      | 41      | 45      |
| 3     | 3          | Sonnet 5.5 | all at once from the step | 31     | 38     | 48      | 46      | 49      | 45      | –       |
| 4     | 4          | Sonnet 5.5 | after the step            | 13     | 18     | 23      | 26      | 31      | 35      | 38      |
| 4     | 4          | Sonnet 5.5 | all at once from the step | 43     | 39     | 41      | 39      | 40      | 39      | –       |
| 9     | 1          | Sonnet 5.5 | after the step            | 42     | 46     | 51      | 54      | 57      | 59      | 62      |
| 9     | 1          | Sonnet 5.5 | all at once from the step | 67     | 67     | 64      | 64      | 63      | 63      | –       |
| 10    | 2          | Sonnet 5.5 | after the step            | 42     | 45     | 50      | 54      | 59      | 62      | 67      |
| 10    | 2          | Sonnet 5.5 | all at once from the step | 66     | 63     | 67      | 67      | 65      | 66      | –       |
| 11    | 3          | Sonnet 5.5 | after the step            | 14     | 18     | 22      | 26      | 30      | 34      | 37      |
| 11    | 3          | Sonnet 5.5 | all at once from the step | 40     | 40     | 38      | 40      | 38      | 38      | –       |
| 12    | 4          | Sonnet 5.5 | after the step            | 13     | 18     | 22      | 26      | 30      | 40      | 44      |
| 12    | 4          | Sonnet 5.5 | all at once from the step | 43     | 43     | 39      | 37      | 40      | 45      | –       |
| 5     | 1          | GPT-6 Luna | after the step            | 42     | 47     | 73      | 76      | 80      | 83      | 86      |
| 5     | 1          | GPT-6 Luna | all at once from the step | 79     | 70     | 79      | 83      | 84      | 85      | –       |
| 6     | 2          | GPT-6 Luna | after the step            | 42     | 47     | 78      | 82      | 87      | 90      | 93      |
| 6     | 2          | GPT-6 Luna | all at once from the step | 75     | –      | 82      | 91      | 89      | 99      | –       |
| 7     | 3          | GPT-6 Luna | after the step            | 14     | 17     | 32      | 37      | 39      | 45      | 48      |
| 7     | 3          | GPT-6 Luna | all at once from the step | 43     | 46     | 53      | 45      | 47      | 50      | –       |
| 8     | 4          | GPT-6 Luna | after the step            | 13     | 28     | 33      | 37      | 41      | 44      | 49      |
| 8     | 4          | GPT-6 Luna | all at once from the step | 34     | 46     | 53      | 50      | 49      | 49      | –       |

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

## Appendix C. Run 3, step by step

As in Appendix A.

**Corridor rooms**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5            | after the step            | 42     | 0      | 0       | 0       | 0       | 0       | 1       |
| 1     | 1          | Sonnet 5.5            | all at once from the step | 0      | 0      | 0       | 0       | 0       | 0       | –       |
| 2     | 2          | Sonnet 5.5            | after the step            | 42     | 0      | 0       | 0       | 0       | 0       | 0       |
| 2     | 2          | Sonnet 5.5            | all at once from the step | 0      | 0      | 0       | 0       | 0       | 0       | –       |
| 3     | 3          | Sonnet 5.5            | after the step            | 14     | 0      | 0       | 0       | 0       | 0       | 0       |
| 3     | 3          | Sonnet 5.5            | all at once from the step | 0      | 0      | 0       | 0       | 0       | 0       | –       |
| 4     | 4          | Sonnet 5.5            | after the step            | 13     | 0      | 0       | 0       | 0       | 0       | 0       |
| 4     | 4          | Sonnet 5.5            | all at once from the step | 0      | 0      | 0       | 0       | 0       | 0       | –       |
| 5     | 1          | DeepSeek adapter, low | after the step            | 42     | 0      | 0       | 0       | 0       | 0       | 0       |
| 5     | 1          | DeepSeek adapter, low | all at once from the step | 42     | 0      | 0       | 0       | 0       | 0       | –       |
| 7     | 3          | DeepSeek adapter, low | after the step            | 14     | 0      | 0       | 0       | 0       | 0       | 0       |
| 7     | 3          | DeepSeek adapter, low | all at once from the step | 0      | 0      | 0       | 0       | 0       | 0       | –       |

**Privacy order**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5            | after the step            | 0.0037 | 0.0000 | 0.0000  | 0.0000  | 0.0000  | 0.0000  | 0.0000  |
| 1     | 1          | Sonnet 5.5            | all at once from the step | 0.0000 | 0.0000 | 0.0000  | 0.0000  | 0.0000  | 0.0000  | –       |
| 2     | 2          | Sonnet 5.5            | after the step            | 0.0037 | 0.0000 | 0.0000  | 0.0000  | 0.0000  | 0.0000  | 0.0000  |
| 2     | 2          | Sonnet 5.5            | all at once from the step | 0.0000 | 0.0000 | 0.0000  | 0.0000  | 0.0000  | 0.0000  | –       |
| 3     | 3          | Sonnet 5.5            | after the step            | 0.0074 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 3     | 3          | Sonnet 5.5            | all at once from the step | 0.0000 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 4     | 4          | Sonnet 5.5            | after the step            | 0.0074 | 0.0000 | 0.0000  | 0.0090  | 0.0085  | 0.0000  | 0.0000  |
| 4     | 4          | Sonnet 5.5            | all at once from the step | 0.0077 | 0.0026 | 0.0000  | 0.0077  | 0.0077  | 0.0000  | –       |
| 5     | 1          | DeepSeek adapter, low | after the step            | 0.0037 | 0.0000 | 0.0064  | 0.0030  | 0.3892  | 0.0000  | 0.0077  |
| 5     | 1          | DeepSeek adapter, low | all at once from the step | 0.0026 | 0.0000 | 0.0000  | 0.0000  | 0.0077  | 0.0026  | –       |
| 7     | 3          | DeepSeek adapter, low | after the step            | 0.0074 | 0.0034 | 0.2628  | 0.0000  | 0.0000  | 0.0000  | 0.0026  |
| 7     | 3          | DeepSeek adapter, low | all at once from the step | 0.0000 | 0.0000 | 0.0077  | 0.0000  | 0.0026  | 0.0000  | –       |

**Walking distance**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5            | after the step            | 9.56   | 9.78   | 10.15   | 10.35   | 10.48   | 10.82   | 11.11   |
| 1     | 1          | Sonnet 5.5            | all at once from the step | 16.53  | 11.12  | 11.18   | 11.69   | 11.25   | 11.13   | –       |
| 2     | 2          | Sonnet 5.5            | after the step            | 9.91   | 9.87   | 10.23   | 10.28   | 10.48   | 10.83   | 11.42   |
| 2     | 2          | Sonnet 5.5            | all at once from the step | 16.53  | 11.27  | 15.16   | 11.53   | 11.06   | 11.12   | –       |
| 3     | 3          | Sonnet 5.5            | after the step            | 7.96   | 9.75   | 10.07   | 10.56   | 10.70   | 10.74   | 11.02   |
| 3     | 3          | Sonnet 5.5            | all at once from the step | 11.14  | 14.58  | 11.36   | 10.96   | 11.04   | 10.96   | –       |
| 4     | 4          | Sonnet 5.5            | after the step            | 7.60   | 13.19  | 14.04   | 10.59   | 10.63   | 10.89   | 11.27   |
| 4     | 4          | Sonnet 5.5            | all at once from the step | 11.65  | 14.89  | 17.79   | 11.72   | 11.11   | 11.28   | –       |
| 5     | 1          | DeepSeek adapter, low | after the step            | 9.56   | 15.72  | 11.18   | 15.93   | 16.06   | 18.74   | 14.88   |
| 5     | 1          | DeepSeek adapter, low | all at once from the step | 15.06  | 16.55  | 18.64   | 18.63   | 17.59   | 17.13   | –       |
| 7     | 3          | DeepSeek adapter, low | after the step            | 7.96   | 16.57  | 11.68   | 18.77   | 18.78   | 18.77   | 17.59   |
| 7     | 3          | DeepSeek adapter, low | all at once from the step | 14.18  | 18.31  | 12.91   | 13.04   | 12.90   | 12.05   | –       |

**Compactness**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 1     | 1          | Sonnet 5.5            | after the step            | 8      | 2      | 8       | 8       | 12      | 16      | 16      |
| 1     | 1          | Sonnet 5.5            | all at once from the step | 2      | 2      | 8       | 34      | 24      | 14      | –       |
| 2     | 2          | Sonnet 5.5            | after the step            | 12     | 2      | 0       | 6       | 12      | 14      | 0       |
| 2     | 2          | Sonnet 5.5            | all at once from the step | 2      | 4      | 2       | 4       | 8       | 10      | –       |
| 3     | 3          | Sonnet 5.5            | after the step            | 16     | 0      | 6       | 2       | 0       | 2       | 0       |
| 3     | 3          | Sonnet 5.5            | all at once from the step | 0      | 0      | 0       | 10      | 0       | 10      | –       |
| 4     | 4          | Sonnet 5.5            | after the step            | 8      | 2      | 6       | 0       | 6       | 2       | 0       |
| 4     | 4          | Sonnet 5.5            | all at once from the step | 2      | 0      | 24      | 2       | 12      | 4       | –       |
| 5     | 1          | DeepSeek adapter, low | after the step            | 8      | 0      | 0       | 48      | 0       | 0       | 0       |
| 5     | 1          | DeepSeek adapter, low | all at once from the step | 28     | 0      | 0       | 0       | 0       | 0       | –       |
| 7     | 3          | DeepSeek adapter, low | after the step            | 16     | 0      | 0       | 0       | 0       | 0       | 0       |
| 7     | 3          | DeepSeek adapter, low | all at once from the step | 0      | 0      | 0       | 0       | 0       | 14      | –       |

## Appendix D. Run 4, step by step

As in Appendix A.

**Corridor rooms**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 5     | 1          | Sonnet 5.5            | after the step            | 42     | 46     | 51      | 56      | 58      | 62      | 65      |
| 5     | 1          | Sonnet 5.5            | all at once from the step | 70     | 46     | 52      | 57      | 59      | 65      | –       |
| 6     | 2          | Sonnet 5.5            | after the step            | 42     | 45     | 50      | 53      | 57      | 60      | 64      |
| 6     | 2          | Sonnet 5.5            | all at once from the step | 43     | 68     | 66      | 54      | 58      | 64      | –       |
| 7     | 3          | Sonnet 5.5            | after the step            | 14     | 18     | 23      | 28      | 31      | 33      | 38      |
| 7     | 3          | Sonnet 5.5            | all at once from the step | 12     | 16     | 22      | 29      | 32      | 37      | –       |
| 8     | 4          | Sonnet 5.5            | after the step            | 13     | 18     | 20      | 24      | 27      | 31      | 34      |
| 8     | 4          | Sonnet 5.5            | all at once from the step | 13     | 18     | 20      | 24      | 27      | 33      | –       |
| 9     | 1          | Opus 5.5              | after the step            | 42     | 0      | 0       | 0       | 0       | 0       | 0       |
| 9     | 1          | Opus 5.5              | all at once from the step | 0      | 0      | 0       | 0       | 0       | 0       | –       |
| 1     | 1          | DeepSeek adapter, low | after the step            | 42     | 0      | 0       | 0       | 0       | 0       | 0       |
| 1     | 1          | DeepSeek adapter, low | all at once from the step | 0      | 0      | 0       | 0       | 0       | 0       | –       |
| 3     | 3          | DeepSeek adapter, low | after the step            | 14     | 0      | 0       | 0       | 0       | 0       | 0       |
| 3     | 3          | DeepSeek adapter, low | all at once from the step | 0      | 0      | 0       | 0       | 0       | 0       | –       |

**Privacy order**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 5     | 1          | Sonnet 5.5            | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 5     | 1          | Sonnet 5.5            | all at once from the step | 0.0026 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 6     | 2          | Sonnet 5.5            | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 6     | 2          | Sonnet 5.5            | all at once from the step | 0.0026 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 7     | 3          | Sonnet 5.5            | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0054  | 0.0051  |
| 7     | 3          | Sonnet 5.5            | all at once from the step | 0.0051 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0051  | –       |
| 8     | 4          | Sonnet 5.5            | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0054  | 0.0051  |
| 8     | 4          | Sonnet 5.5            | all at once from the step | 0.0051 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0051  | –       |
| 9     | 1          | Opus 5.5              | after the step            | 0.0037 | 0.0000 | 0.0000  | 0.0000  | 0.0000  | 0.0000  | 0.0000  |
| 9     | 1          | Opus 5.5              | all at once from the step | 0.0000 | 0.0000 | 0.0000  | 0.0000  | 0.0000  | 0.0000  | –       |
| 1     | 1          | DeepSeek adapter, low | after the step            | 0.0037 | 0.0103 | 0.0000  | 0.0000  | 0.0028  | 0.0081  | 0.0077  |
| 1     | 1          | DeepSeek adapter, low | all at once from the step | 0.0077 | 0.0077 | 0.0077  | 0.0000  | 0.0026  | 0.0077  | –       |
| 3     | 3          | DeepSeek adapter, low | after the step            | 0.0074 | 0.0034 | 0.0032  | 0.0120  | 0.0085  | 0.0081  | 0.0102  |
| 3     | 3          | DeepSeek adapter, low | all at once from the step | 0.0077 | 0.0026 | 0.0026  | 0.0000  | 0.0077  | 0.0077  | –       |

**Walking distance**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 5     | 1          | Sonnet 5.5            | after the step            | 9.56   | 9.88   | 10.40   | 10.94   | 11.23   | 11.68   | 12.12   |
| 5     | 1          | Sonnet 5.5            | all at once from the step | 11.70  | 13.88  | 13.79   | 13.38   | 12.60   | 12.01   | –       |
| 6     | 2          | Sonnet 5.5            | after the step            | 9.91   | 10.27  | 10.80   | 11.15   | 11.65   | 12.02   | 12.49   |
| 6     | 2          | Sonnet 5.5            | all at once from the step | 14.58  | 12.15  | 12.40   | 13.77   | 12.95   | 12.40   | –       |
| 7     | 3          | Sonnet 5.5            | after the step            | 7.96   | 8.20   | 8.34    | 8.44    | 8.57    | 8.76    | 8.95    |
| 7     | 3          | Sonnet 5.5            | all at once from the step | 14.93  | 11.77  | 11.63   | 10.81   | 9.81    | 8.86    | –       |
| 8     | 4          | Sonnet 5.5            | after the step            | 7.60   | 7.81   | 8.04    | 8.22    | 8.43    | 8.57    | 8.75    |
| 8     | 4          | Sonnet 5.5            | all at once from the step | 10.53  | 9.95   | 10.24   | 10.53   | 9.28    | 8.74    | –       |
| 9     | 1          | Opus 5.5              | after the step            | 9.56   | 9.80   | 10.22   | 10.61   | 11.57   | 12.78   | 14.20   |
| 9     | 1          | Opus 5.5              | all at once from the step | 13.76  | 11.08  | 13.21   | 11.08   | 14.36   | 11.59   | –       |
| 1     | 1          | DeepSeek adapter, low | after the step            | 9.56   | 13.11  | 14.37   | 10.73   | 14.33   | 17.66   | 17.02   |
| 1     | 1          | DeepSeek adapter, low | all at once from the step | 11.73  | 17.01  | 12.42   | 12.01   | 15.28   | 15.04   | –       |
| 3     | 3          | DeepSeek adapter, low | after the step            | 7.96   | 16.02  | 15.50   | 15.78   | 10.81   | 16.85   | 12.87   |
| 3     | 3          | DeepSeek adapter, low | all at once from the step | 12.20  | 20.19  | 18.80   | 17.59   | 14.85   | 18.06   | –       |

**Compactness**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 5     | 1          | Sonnet 5.5            | after the step            | 8      | 8      | 12      | 16      | 12      | 12      | 12      |
| 5     | 1          | Sonnet 5.5            | all at once from the step | 2      | 20     | 26      | 22      | 18      | 16      | –       |
| 6     | 2          | Sonnet 5.5            | after the step            | 12     | 10     | 14      | 16      | 18      | 18      | 18      |
| 6     | 2          | Sonnet 5.5            | all at once from the step | 30     | 10     | 18      | 24      | 22      | 18      | –       |
| 7     | 3          | Sonnet 5.5            | after the step            | 16     | 12     | 14      | 10      | 8       | 8       | 8       |
| 7     | 3          | Sonnet 5.5            | all at once from the step | 12     | 18     | 24      | 10      | 14      | 6       | –       |
| 8     | 4          | Sonnet 5.5            | after the step            | 8      | 4      | 4       | 6       | 8       | 6       | 6       |
| 8     | 4          | Sonnet 5.5            | all at once from the step | 30     | 6      | 24      | 22      | 14      | 4       | –       |
| 9     | 1          | Opus 5.5              | after the step            | 8      | 2      | 0       | 2       | 4       | 4       | 0       |
| 9     | 1          | Opus 5.5              | all at once from the step | 0      | 2      | 2       | 6       | 0       | 8       | –       |
| 1     | 1          | DeepSeek adapter, low | after the step            | 8      | 2      | 28      | 0       | 0       | 2       | 58      |
| 1     | 1          | DeepSeek adapter, low | all at once from the step | 0      | 8      | 0       | 0       | 6       | 2       | –       |
| 3     | 3          | DeepSeek adapter, low | after the step            | 16     | 2      | 6       | 0       | 0       | 14      | 12      |
| 3     | 3          | DeepSeek adapter, low | all at once from the step | 0      | 62     | 2       | 0       | 0       | 0       | –       |

## Appendix E. Run 5, step by step

As in Appendix A.

**Corridor rooms**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 5     | 1          | Sonnet 5.5            | after the step            | 42     | 45     | 49      | 54      | 58      | 63      | 67      |
| 5     | 1          | Sonnet 5.5            | all at once from the step | 67     | 64     | 64      | 66      | 66      | 67      | –       |
| 7     | 3          | Sonnet 5.5            | after the step            | 14     | 18     | 23      | 28      | 31      | 35      | 38      |
| 7     | 3          | Sonnet 5.5            | all at once from the step | 40     | 27     | 41      | 41      | 39      | 40      | –       |
| 9     | 1          | Opus 5.5              | after the step            | 42     | 46     | 50      | 55      | 59      | 61      | 65      |
| 9     | 1          | Opus 5.5              | all at once from the step | 41     | 45     | 65      | 53      | 64      | 64      | –       |
| 1     | 1          | DeepSeek adapter, low | after the step            | 42     | 44     | 47      | 50      | 49      | 49      | 51      |
| 1     | 1          | DeepSeek adapter, low | all at once from the step | 63     | 69     | 47      | 65      | 57      | 49      | –       |
| 3     | 3          | DeepSeek adapter, low | after the step            | 14     | 15     | 17      | 28      | 31      | 38      | 40      |
| 3     | 3          | DeepSeek adapter, low | all at once from the step | 14     | 15     | 17      | 28      | 31      | 38      | –       |

**Privacy order**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 5     | 1          | Sonnet 5.5            | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 5     | 1          | Sonnet 5.5            | all at once from the step | 0.0026 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 7     | 3          | Sonnet 5.5            | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0054  | 0.0051  |
| 7     | 3          | Sonnet 5.5            | all at once from the step | 0.0051 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0051  | –       |
| 9     | 1          | Opus 5.5              | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 9     | 1          | Opus 5.5              | all at once from the step | 0.0026 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 1     | 1          | DeepSeek adapter, low | after the step            | 0.0037 | 0.0034 | 0.0032  | 0.0030  | 0.0028  | 0.0027  | 0.0026  |
| 1     | 1          | DeepSeek adapter, low | all at once from the step | 0.0026 | 0.0026 | 0.0026  | 0.0026  | 0.0026  | 0.0026  | –       |
| 3     | 3          | DeepSeek adapter, low | after the step            | 0.0074 | 0.0068 | 0.0064  | 0.0060  | 0.0057  | 0.0054  | 0.0051  |
| 3     | 3          | DeepSeek adapter, low | all at once from the step | 0.0051 | 0.0051 | 0.0051  | 0.0051  | 0.0051  | 0.0051  | –       |

**Walking distance**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 5     | 1          | Sonnet 5.5            | after the step            | 9.56   | 9.95   | 10.39   | 10.70   | 10.92   | 11.25   | 11.58   |
| 5     | 1          | Sonnet 5.5            | all at once from the step | 11.46  | 11.78  | 12.18   | 11.78   | 11.33   | 11.76   | –       |
| 7     | 3          | Sonnet 5.5            | after the step            | 7.96   | 8.09   | 8.24    | 8.44    | 8.61    | 8.76    | 8.92    |
| 7     | 3          | Sonnet 5.5            | all at once from the step | 8.95   | 10.15  | 8.80    | 8.86    | 8.91    | 8.87    | –       |
| 9     | 1          | Opus 5.5              | after the step            | 9.56   | 9.93   | 10.29   | 10.85   | 11.26   | 11.59   | 11.93   |
| 9     | 1          | Opus 5.5              | all at once from the step | 13.39  | 14.30  | 11.59   | 12.86   | 12.00   | 12.06   | –       |
| 1     | 1          | DeepSeek adapter, low | after the step            | 9.56   | 10.23  | 11.05   | 11.51   | 11.97   | 12.49   | 12.92   |
| 1     | 1          | DeepSeek adapter, low | all at once from the step | 13.32  | 12.36  | 13.77   | 14.13   | 12.72   | 12.89   | –       |
| 3     | 3          | DeepSeek adapter, low | after the step            | 7.96   | 8.32   | 8.67    | 10.65   | 11.06   | 11.20   | 11.53   |
| 3     | 3          | DeepSeek adapter, low | all at once from the step | 12.84  | 12.51  | 12.02   | 12.93   | 12.55   | 11.80   | –       |

**Compactness**

| Chain | Seed house | Model                 | House                     | step 0 | step 5 | step 10 | step 15 | step 20 | step 25 | step 30 |
| ----- | ---------- | --------------------- | ------------------------- | ------ | ------ | ------- | ------- | ------- | ------- | ------- |
| 5     | 1          | Sonnet 5.5            | after the step            | 8      | 12     | 10      | 10      | 10      | 12      | 10      |
| 5     | 1          | Sonnet 5.5            | all at once from the step | 6      | 10     | 12      | 10      | 10      | 12      | –       |
| 7     | 3          | Sonnet 5.5            | after the step            | 16     | 10     | 12      | 16      | 8       | 4       | 2       |
| 7     | 3          | Sonnet 5.5            | all at once from the step | 18     | 16     | 8       | 16      | 4       | 2       | –       |
| 9     | 1          | Opus 5.5              | after the step            | 8      | 10     | 8       | 10      | 6       | 6       | 6       |
| 9     | 1          | Opus 5.5              | all at once from the step | 34     | 10     | 10      | 20      | 4       | 4       | –       |
| 1     | 1          | DeepSeek adapter, low | after the step            | 8      | 10     | 14      | 14      | 14      | 16      | 14      |
| 1     | 1          | DeepSeek adapter, low | all at once from the step | 24     | 10     | 30      | 34      | 12      | 22      | –       |
| 3     | 3          | DeepSeek adapter, low | after the step            | 16     | 12     | 18      | 16      | 14      | 16      | 10      |
| 3     | 3          | DeepSeek adapter, low | all at once from the step | 40     | 32     | 32      | 16      | 14      | 16      | –       |

## Reproducibility

The data are in `runs_100_rooms/` (run 1), `runs_100_rooms_no_hallways/` (run 2), `runs_100_rooms_refactor/` (run 3),
`runs_100_rooms_refactor_cost/` (run 4) and `runs_100_rooms_cost/` (run 5); every agent call is one JSON record with its
script, the house it produced, the house's scores and the agent's token usage. The seed houses and the code that made
them are in `runs_100_rooms/seeds/`. The chains were run with `python -m house.run_100_rooms` as described in [running
the experiment](docs/running-the-experiment.md#70-to-100-room-chains); the DeepSeek chains used the standalone adapter.
This report is generated by `python paper/build_report_100_rooms.py` from `paper/REPORT_100_rooms.template.md`.