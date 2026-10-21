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
| Corridor rooms | How often you must walk through a room that is not your destination | Bathroom reachable only through a bedroom |
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
