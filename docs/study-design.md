# Study design: patching versus planning, in a world of houses

Nuno Oliveira · first written 19 October 2026

This document defines the house world (its language, rules and scores) and the experiment run in it. The results are in [the report](../REPORT.md); how to run the experiment is in [running the experiment](running-the-experiment.md). The analysis plans of the first runs refer to this document by its earlier file name, `HOUSE_DSL.md`.

## Hypothesis

An AI agent asked to make a local change to an existing artefact will produce a worse result than an agent asked to build the same final requirements from scratch, even when both have the same rules, tools and quality measures. The cause is the framing of the request, not a lack of information.

The house is a metaphor for software built by exploratory prototyping:

- Early on, nobody (human or agent) knows the final ontology of the product.
- Behaviour attaches to data locally. When a second behaviour needs the same data, it gets pulled out to a shared place that is never named as a concept.
- The result works, but has no structure: lots of global data and functions pointing at it.
- Each new request is patched in locally. Eventually someone has to stop and redesign from scratch, using the insights the prototype revealed.

This cost is invisible to managers who only see the working prototype, and reviewers sense it without being able to name it. The house model makes it visible: a bathroom patched into an existing house versus a house designed with that bathroom from the start.

## The world

A house is a single floor laid out on a small grid, where every room occupies one square cell of the same size.

**Terms:** a *cell* is one square of the grid; a *room* is what occupies it.

- **Grid:** 5×5 (25 cells), enough room for the house to grow over seven change requests without filling the grid. Checking one house against the rules and scores must be near-instant; enumerating every layout is optional.
- **Room types:** living room, kitchen, bedroom, bathroom, and hallway in runs that allow hallways. Hallways are a setting of each run: a run that allows them (`--hallways`) uses `house/prompt_template_hallways.txt`, and its scripts may place hallways; otherwise a script that places one is rejected. In the first run, which allowed them, every final house had four to seven hallways: a free hallway fixes any access problem, so patched and planned houses both ended up as rooms hung off a spine of hallways, and the hallways hid any difference between them. Without hallways every cell holds a requested room, and a house is good or bad by where its rooms are and how its doors join them.
- **Adjacency:** two cells are neighbours if they share an edge (left, right, above, below). "Next to" always means this.
- **No merging:** rooms are never merged. Every room is exactly one cell, so a room touches at most four others. The language has no command that joins two rooms.

## The language

A program is an ordered sequence of commands; running it builds the house step by step, following the order of real construction: shell, then interior walls, then openings.

**Commands** (mirror physical construction):

| Add | Remove |
| --- | --- |
| place a room | remove a room |
| add door to wall | remove door |
| add window to wall | remove window |

Walls are implied, never written: a wall stands on every edge between two different rooms and between a room and the outside. The first runs also had commands to add and remove walls, which changed nothing, and composite commands such as `add bathroom next to R4`; no agent used any of them, so they were dropped.

A door belongs to a wall, so it is automatically shared by the two spaces on either side. A door in an outer wall leads outside.

## Hard rules (validity)

A house is valid only if a person can walk in through the front door, visit every room, and walk back out. This is the core rule; the others support it.

1. **Circulation:** every room is reachable from the entrance through doors.
2. **No detached rooms:** every room shares a wall with the rest of the house.
3. **Every room has a door:** at least one, shared with a neighbouring room.
4. **One entrance:** only the living room may have a door in an outer wall, so every house needs a living room.
5. **One kitchen:** a house never has more than one kitchen. A house with no kitchen is allowed.
6. **Requested rooms:** the finished house has exactly the rooms that were asked for. A `build:` request lists each room type and how many; an `add:` request means the rooms the house already had plus the ones listed. Rooms may be removed or rebuilt on the way, but the final count of each requested type must match.
7. **Rules are rechecked after every change,** including removals. Anything not written down is allowed.

A badly placed bathroom must still pass all of these. Validity is the equivalent of "the code runs"; quality is measured separately.

## Quality score (fitness functions)

Among valid houses, quality is measured by four fitness functions. They are used only to judge finished designs; agents never see a score while designing.

**Good-house criteria (given to both agents as guidance, not hard rules):** bedrooms, bathrooms and the kitchen are destinations, never passages. Both agents receive the same written criteria so they can judge their own placements; neither gets an unfair advantage. Because these are criteria rather than rules, the bad house (living room → bedroom → bedroom → bathroom → bedroom) stays possible, so the failure can be observed.

| Fitness function | What it measures | Typical patch symptom |
| --- | --- | --- |
| Corridor rooms | How many bedrooms, bathrooms and kitchens lie on a best route between two other rooms (one crossing as few of them as possible) | Bathroom reachable only through a bedroom |
| Privacy order | Public rooms (living room, kitchen) near the entrance, private rooms (bedrooms, bathrooms) further in | Bathroom off the living room, bedroom as a passage |
| Walking distance | Average number of doors between every pair of rooms | New room added at the far end of a chain |
| Compactness | How close the outline is to a compact shape (perimeter against area) | Bathroom sticking out as an add-on |

The four scores are reported separately, never combined. Together with the drawings, they are the only way to characterise a solution.

## Experiment design

The only variable is how the task is framed; information, rules and good-house principles are identical for both agents. This avoids staging a failure by starving the second agent of context.

|  | Patch agent | Planned agent |
| --- | --- | --- |
| Starts from | An existing valid house built by another agent | An empty grid |
| Request | One room at a time, such as `add: bathroom` | `build:` the original rooms plus every room added |
| Professional briefing (language, hard rules, good-house principles and why) | Yes | Yes |
| Score feedback while designing | No | No |
| Attempts | One | One |
| Allowed to demolish and rebuild | Yes | Not applicable |

**Building and demolishing are free.** No command costs anything, whether it builds or removes. Putting a price on change would be a methodological error: the experiment asks whether agents have an intrinsic bias toward locality, and a price would give them an outside reason to keep their changes small. With nothing to pay, any preference for patching is the agent's own habit.

**The agent is a professional, judged on design.** Each agent is briefed as an experienced house builder who already knows what makes a good house and why. It hands in its whole program in one go, as a single design, with no trial and error and no checks along the way. The design is then checked against the hard rules and scored once. The experiment studies how the agent designs the change, not how it implements it.

Procedure:

1. A first agent builds a base house from a room list.
2. The patch agent receives the base house and one change request.
3. The planned agent receives the final room list and builds from scratch.
4. Score both houses with the fitness functions.
5. Repeat with a sequence of seven change requests, a fresh patch agent each time, to see whether the gap grows (accumulating debt). One more agent receives the base house and all seven rooms in a single request.
6. Repeat the whole sequence over several base houses (six chains per run), and across agents and effort levels.

[Running the experiment](running-the-experiment.md) gives the exact steps and requests of a chain.

**Prediction:** the patch agent's houses score worse than the planned agent's, and the gap widens with each change request, even though rebuilding was always allowed.

## The 70-to-100-room runs

The same question, with houses big enough that redesigning is no longer casual: houses of 70 rooms grown to 100 on a 15×15 grid (225 cells, rows A to O), with the hard rules and four scores above. There are five runs. In three of them building and demolishing cost nothing: in the hallway run (data in `runs_100_rooms/`) hallways can be built; in the no-hallways run (data in `runs_100_rooms_no_hallways/`) they cannot; the reorganising run (data in `runs_100_rooms_refactor/`) is the hallway run with one sentence added to the prompt, asking every agent to reorganise the house before adding to it. The cost run (data in `runs_100_rooms_refactor_cost/`) is the reorganising run with a price on every command. The cost-only run (data in `runs_100_rooms_cost/`) is the hallway run with a price on every command.

**Question.** On the 5×5 grid, with building and demolishing free, adding rooms one at a time never ended worse than planning, and the agents showed no built-in preference for local changes. Does adding the rooms one at a time end worse than adding all the remaining rooms at once to the same house? And does the answer depend on the house the agents start from: one that grew under a tight budget, or one that grew without cost constraints?

**Why no hallways.** On the 5×5 grid, taking hallways away made agents either attach each new room to the house or tear the house down and rebuild it when attaching got hard. Does that make agents redesign 70-room houses too, or does the size of the house keep them from redesigning at all?

**Why ask to reorganise.** In the hallway run neither kind of agent redesigned the house: the one-room agents attached rooms and the all-at-once agents hung a hallway wing behind the house they received. Asked outright to reorganise first, do the agents redesign, and does adding the rooms one at a time still end worse than adding them all at once?

**Why cost.** On the 5×5 grid, pricing every command made the patch agents purely local; in the world with hallways they stopped refactoring and the stepwise houses ended worse than planning. Asked to reorganise and told what every command costs, do the agents still rebuild, and does adding the rooms one at a time then end worse than adding them all at once? The cost-only run asks the same price without the reorganise sentence, so the two effects can be told apart.

**Expectation.** Written before the hallway run: as in the free 5×5 runs, the house after step 30 scores no worse than the house built all at once from step 0. All five runs are described, not tested.

**Prompt.** `house/prompt_template_100_rooms.txt` is the prompt of the priced runs with hallways (`house/prompt_template_hallways.txt` at commit `25e3cef`) with the cost section taken out, the grid size set to 15, and one line added after the room types: "Room ids: R followed by a number, as in R1, R2, R3." The no-hallways run uses `house/prompt_template_100_rooms_no_hallways.txt`, the same prompt with two changes: rule 6 says hallways may be removed but not added, and the language section says "No hallway can be built; the ones already in the layout may be removed." The reorganising run uses `house/prompt_template_100_rooms_refactor.txt`, the hallway run's prompt with one sentence placed just before the request, in every call: "Before you add anything, reorganise the existing house to reduce its complexity, keeping the exact same final number of rooms (excluding hallways, whose number can change)." The cost run uses `house/prompt_template_100_rooms_refactor_cost.txt`, that prompt with the priced runs' cost section added: every command costs something, whether it builds or removes, a room or the removal of a room 4 (a room is four walls), a door or a window 1, and the total cost of the script also counts. The cost-only run uses `house/prompt_template_100_rooms_cost.txt`, the hallway run's prompt with the same cost section added. In the no-hallways run, a script that builds a hallway is rejected ("there are no hallways in this house") and tried again with a fresh agent, like any other rejected script.

**Seed houses.** Four seed houses of 70 rooms (living room, kitchen, 34 bedrooms, 34 bathrooms), made in code, not by agents. Each starts from the 11-room house that ended one chain of the priced runs and grew one room at a time on the 15×15 grid:

* Houses 1 and 2 grew under a tight budget: each room was added the way one of the priced runs' agents added a room, that is the same kind of change, next to the same type of room, as near the entrance, its cell touching as many rooms. House 1 starts from chain 1 of the priced run, house 2 from chain 4 of its repeat.
* Houses 3 and 4 grew without cost constraints: of every five rooms, in a random order, three were added by the change that gave the best scores over the whole house, one by the change that gave the best scores over the rooms within two cells of it, and one by a change chosen at random. Scores were ranked corridor rooms first, then privacy order, walking distance and compactness. Houses 3 and 4 start from chains 3 and 5 of the priced run.
* Of each kind, 12 candidates were grown, one from each priced-run chain. Each candidate was finished to 100 rooms 10 times by each of four simulated builders (the three above, and one copying the agents of the first 5×5 run). The two chosen of each kind are those whose finished houses varied most in corridor rooms: the houses whose outcome depends most on how they are extended.

The seed houses hold 5, 5, 47 and 45 hallways besides their 70 other rooms. All five runs use them unchanged, so the no-hallways run is not a house without hallways but a world in which none can be built: the hallways a seed house has can be used (a door onto one) or removed. The seed houses and the code that made them are in `runs_100_rooms/seeds/`, with copies in `runs_100_rooms_no_hallways/seeds/`, `runs_100_rooms_refactor/seeds/`, `runs_100_rooms_refactor_cost/seeds/` and `runs_100_rooms_cost/seeds/`.

**Chains.** Each chain starts from one seed house and has two kinds of agent:

* **One room at a time:** steps 1 to 30 each add one room to the house the previous step left (the seed house for step 1): `add: bedroom`, `add: bathroom` and so on in turn. After step 30 the house has 100 rooms (49 bedrooms, 49 bathrooms).
* **All at once:** from the house left after each of steps 0 to 28 (step 0 is the seed house), one agent adds all the rooms still missing in a single request, such as `add: bedroom x15, bathroom x15` from step 0. After step 29 the one room missing would be the same request as step 30.

A chain has 59 calls, made in this order: all at once from step 0, step 1, all at once from step 1, step 2, and so on. Every agent is fresh, with no tools, no memory and no score feedback. A failed call (script rejected or house invalid) is tried again with a fresh agent, up to 3 tries. If a one-room step still fails, that chain's one-room steps stop, and the all-at-once calls from the steps already reached are still made. A reply cut off by the output limit is recorded as cut off, not as an invalid house. No agent builds the 100-room house from scratch.

**Agents.** The Sonnet and GPT-6 Luna chains are at medium effort. DeepSeek chains 5 and 7 in the hallway run and in
the reorganising run (seed houses 1 and 3; chains 6 and 8 not run) and chains 1 and 3 in the cost run and in the
cost-only run (seed houses 1 and 3) use a standalone DeepSeek adapter at low thinking, with the model `deepseek-flash`
(DeepSeek-V4.1-Flash-1017): it posts the house prompt to DeepSeek's Anthropic-compatible
API with thinking enabled at low effort, and no Claude Code system or environment wrapper. It is a separate harness
and is reported separately. DeepSeek is many times slower than Sonnet (a mean of 92 seconds per call against 18, and of 1.6 hours per chain against
0.3), and it was run at low thinking because at high effort it was even slower.

| Run          | Chains | Seed houses | Model          | Harness                                                        |
| ------------ | ------ | ----------- | -------------- | -------------------------------------------------------------- |
| Hallways     | 1–4    | 1–4         | Sonnet 5.5     | Claude Code 2.1.310                                            |
| Hallways     | 5, 7   | 1, 3        | deepseek-flash | DeepSeek API adapter (low effort)                              |
| No hallways  | 1–4    | 1–4         | Sonnet 5.5     | Claude Code 2.1.311 (chains 1 and 3), 2.1.312 (chains 2 and 4) |
| No hallways  | 5–8    | 1–4         | GPT-6 Luna     | GitHub Copilot CLI 1.0.105                                     |
| No hallways  | 9–12   | 1–4         | Sonnet 5.5     | Claude Code 2.1.314                                            |
| Reorganising | 1–4    | 1–4         | Sonnet 5.5     | Claude Code 2.1.314 (chain 1), 2.1.319 (chains 2–4)            |
| Reorganising | 5, 7   | 1, 3        | deepseek-flash | DeepSeek API adapter (low effort)                              |
| Cost         | 1, 3   | 1, 3        | deepseek-flash | DeepSeek API adapter (low effort)                              |
| Cost         | 5–8    | 1–4         | Sonnet 5.5     | Claude Code 2.1.322                                            |
| Cost only    | 1, 3   | 1, 3        | deepseek-flash | DeepSeek API adapter (low effort)                              |
| Cost only    | 5, 7   | 1, 3        | Sonnet 5.5     | Claude Code 2.1.322                                            |

The models are reported separately, never pooled.

## System and interaction

The agent never receives feedback: it receives information (layout plus request) and sends back one script. The system builds it, draws it in ASCII and scores it.

**Use cases:**

1. **Initial build:** empty grid plus a room list → agent sends a script → house is built, drawn and scored.
2. **Change request (patch agent):** current layout plus one request (for example "add: bathroom") → script → drawn and scored. Repeated for each further request (another bedroom, and so on).
3. **Planned build (comparison agent):** a separate agent gets an empty grid plus the final room list, including every room the patch agent received piece by piece → script → drawn and scored.

The whole sequence is repeated many times; drawings and scores are saved automatically rather than by manual screenshots.

**Fresh agent per request.** Each change request goes to a new agent that sees only the current layout and the request, never earlier conversations, so its decisions are not polluted by history.

**HTTP server:**

| Endpoint | Purpose |
| --- | --- |
| `GET /layout` | Returns the current layout as text, including walls and doors, not only room types |
| `POST /script` | Accepts a script in the house language, builds the house, renders it in ASCII and computes the four scores |
| `PUT /layout` | Loads a layout to start from (an empty body resets to the empty grid); used to give each agent its starting house |

**Layout format** (what `GET /layout` returns). Rows are A to E, columns 1 to 5. Each cell shows the id of the room on it, or `.` if empty. Walls are implied: a wall stands on every edge between cells of different rooms, and on every edge between a room and the outside. Doors and windows are listed by the edge they sit on.

```
grid 5x5
     1    2    3    4    5
A    R1   R2   .    .    .
B    R3   .    .    .    .
C    .    .    .    .    .
D    .    .    .    .    .
E    .    .    .    .    .

rooms
R1  living room   A1
R2  kitchen       A2
R3  bedroom       B1

doors
A1|north          entrance
A1|A2
A1|B1

windows
A2|north
B1|west
```

The example is a valid house of three rooms: the entrance is in the living room, and the kitchen and the bedroom both open off it. An empty grid has all cells `.` and empty `rooms`, `doors` and `windows` lists.

**Command syntax** (what `POST /script` accepts, one command per line):

```
room R6 bedroom C2          place a new room on an empty cell; walls go up around it
remove room R6              clear the room's cells and everything on its walls
door B1|B2                  add a door in the wall between two cells
door A1|north               add a door in an outer wall (living room only)
remove door B1|B2
window B2|east              add a window in an outer wall
remove window B2|east
```

**Standard prompt template** (identical for Claude, Codex, or any agent; preferred over a skill so it is not tied to one vendor):

- **Fixed part:** you are a professional house builder; the language; the hard rules; the good-house principles and why they matter.
- **Variable slots:** current layout (from `GET /layout`) and a structured request, such as `build: living room, kitchen, bedroom ×2, bathroom` or `add: bathroom`, never a free-form sentence.

**Prompt template** (fixed text, with two slots filled per run):

```
You are an experienced, professional house builder. You design single-floor
houses on a 5x5 grid of cells using the house language below. You get one
attempt: reply with a single script containing your whole design. You will
receive no feedback.

RULES (a house that breaks any rule is invalid)
1. Every room is reachable from the entrance through doors.
2. Every room shares a wall with the rest of the house.
3. Every room has at least one door, shared with a neighbouring room.
4. Only the living room may have a door in an outer wall.
5. A house never has more than one kitchen.
6. The finished house has exactly the rooms requested: for "build:" the
   listed number of each room type, for "add:" the rooms already in the
   current layout plus the ones listed. You may remove, replace or rebuild
   rooms along the way; only the final count of each requested room type
   matters.
Anything not forbidden is allowed.

GOOD-HOUSE PRINCIPLES (your work is judged by these)
- Bedrooms, bathrooms and the kitchen are destinations, never passages:
  nobody should have to walk through one to reach another room.
- Public rooms (living room, kitchen) sit near the entrance; private rooms
  (bedrooms, bathrooms) sit further in.
- Any two rooms should be as few doors apart as possible.
- Keep the house compact, with nothing sticking out.

You may change anything in the current layout.

LANGUAGE
Room types: living room, kitchen, bedroom, bathroom. There are no hallways.
<command syntax reference>

LAYOUT FORMAT
<layout format reference>

CURRENT LAYOUT
{{LAYOUT}}

REQUEST
{{REQUEST}}

Reply with the script only, one command per line.
```

Slot values by use case:

| Use case | `{{LAYOUT}}` | `{{REQUEST}}` |
| --- | --- | --- |
| Initial build | Empty grid | `build: living room, kitchen, bedroom x2, bathroom` |
| Change request | Output of `GET /layout` | `add: bathroom` (one item per run) |
| Planned build | Empty grid | `build:` the initial rooms plus every requested addition |

## Visualisation

Every program renders as an ASCII floor plan: walls, doors, windows and room labels drawn with plain characters, so the difference between a patched and a planned house is visible at a glance. No graphical front end. A side-by-side view (patched and planned) with the four scores underneath is the core exhibit.

## Implementation

Python. The interpreter, rule checker, scores and ASCII renderer are plain Python, and a small HTTP server exposes the two endpoints. Type hints and dataclasses make the house model and the commands explicit.
