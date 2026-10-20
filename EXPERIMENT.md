# Running the experiment

## What is compared

One **chain** is ten fresh agents. The patch requests alternate between bedrooms and bathrooms, and they only add:
what to demolish or rebuild along the way is the agent's own decision.

| Step | Agent starts from | Request |
|---|---|---|
| A | empty grid | `build: living room, kitchen, bedroom, bathroom` (one bedroom) |
| B, D, F, H | the previous agent's house | `add: bedroom` |
| C, E, G | the previous agent's house | `add: bathroom` |
| I | empty grid | `build: living room, kitchen, bedroom x5, bathroom x4`: A's rooms plus every room added by B to H. It does not depend on what the patching agents actually built. |
| J | A's house | `add: bedroom x4, bathroom x3`: everything B to H added one by one, asked for in a single request. Run after A; J does not depend on B to H. |

The question is whether the house patched step by step (H), the house patched in one go (J) and the house planned from
scratch (I) differ on the four scores. The requests and the steps are defined at the top of `house/experiment.py`.

The grid is 5×5. The analysis plan of the run reported in `REPORT.md` is `paper/ANALYSIS_PLAN.md`; its data are in `runs/`.

The language no longer has hallways (see `HOUSE_DSL.md`, room types). The run without them has its own plan,
`paper/ANALYSIS_PLAN_no_hallways.md`, and its own data folder: pass `--runs runs_no_hallways` to both the server and
`house.run_agents`. The houses in `runs/` still load, so `REPORT.md` can be rebuilt.

Building and demolishing now cost (`PRICES` in `house/commands.py`: a room 4, a door or a window 1, whether built or
removed), and the agents are told so. The run with costs has its own plan, `paper/ANALYSIS_PLAN_cost.md`, and data
folder: `--runs runs_cost`. Each record holds the cost of its script, and the report has a cost column.

A run with hallways passes `--hallways` to `house.run_agents` (and to `house.experiment prompt` and `send`): the agents
get `house/prompt_template_hallways.txt`, and every script is sent with `hallways=1`, so the server lets it place
hallways and the record says so. The run with costs and hallways: plan `paper/ANALYSIS_PLAN_cost_hallways.md`, data
`--runs runs_cost_hallways`.

## Agent settings (identical for every agent in a comparison)

- Model: **Sonnet 5.5**, effort: **medium**. The run label records them (`sonnet55-medium-c1-B`).
  For a later run with another model or effort, pass `--model opus55 --effort high` (no `-` inside either name).
- A fresh conversation for every step. **Memory off.** No tools, no access to this project: the agent gets only
  the prompt and answers with text.
- Save the agent's reply to a file exactly as it wrote it. Do not edit it.

## Steps, for chain N = 1, 2, 3

Start the server once, in its own terminal, and leave it running:

```
.venv/bin/python -m house.server
```

For each step S in A to J, in that order:

```
.venv/bin/python -m house.experiment prompt --chain N --step S      # paste the output into a fresh agent
.venv/bin/python -m house.experiment send   --chain N --step S reply.txt
```

`send` puts the right starting house on the server, sends the script together with the request it answers (so the
server can check the requested rooms, rule 6), and tells you how it went:

- `valid.` -> go to the next step.
- `script REJECTED` or `house INVALID` -> run the same step again with a **fresh agent** (new prompt, new reply file).
  Every try is recorded, and the report counts them. Only the last valid house is measured and passed on.

The agent never sees any of this: it gets one prompt, with no feedback, and gives one reply.

## Results

```
.venv/bin/python -m house.experiment report
```

Per chain and averaged over chains: tries, number of commands, the four scores for A to E, the D-E gap,
and drawings of A, D and E side by side. Everything is also in `runs/` (one JSON file per script sent).

## Tokens

`python -m house.run_agents` calls each agent with `--output-format json` and saves its token usage and cost in
that run's record (`agent_usage`). The report ends each model's section with a table of calls, input tokens (new plus
cached), output tokens (thinking included), thinking tokens and cost in dollars, by step, in total and per chain.
Failed tries count, because they cost tokens too. Runs made by hand with `send` have no usage, so they are left out.
