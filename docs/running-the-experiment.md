# Running the experiment

How to run chains of agents, where the data and analysis plan of each run are kept, and how to rebuild the report.
The house world itself (language, rules, scores) is defined in the [study design](study-design.md).

## Setup

Python 3.9 or later. The code uses only the standard library; the tests need pytest.

```
python3 -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest -q
```

The agents are called through the Claude Code CLI (`claude -p`), which must be installed and logged in.

## One chain

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

## Agent settings

The same for every agent in a run:

- **Model and effort:** Claude Sonnet 5.5 at medium effort, unless the run says otherwise. Every record is labelled
  with model, effort, chain and step, such as `sonnet55-medium-c1-B`, so runs with other settings stay apart.
- **A fresh agent for every step:** a new `claude -p` call with no tools, no memory, no settings, no MCP servers, no
  saved session and an empty working folder. The agent gets the prompt and nothing else, and answers with text.
- **No feedback:** the reply is sent to the server exactly as written. If the script is rejected or the house is
  invalid, the step is tried again with another fresh agent, up to `--max-tries` (default 3), and a chain stops when a
  step still fails. Every try is recorded; only the last valid house is measured and passed on.

## Running with agents

Start the server in its own terminal, with the folder the run's data go to, and leave it running:

```
.venv/bin/python -m house.server --runs runs_new
```

Then run the chains:

```
.venv/bin/python -m house.run_agents --chains 6 --effort medium --runs runs_new
```

| Option | Meaning |
|---|---|
| `--chains`, `--first-chain` | how many chains, and the number of the first one (to add chains to a run) |
| `--steps` | run only these steps, e.g. `--steps I J` |
| `--model`, `--effort` | the agent, e.g. `--model opus55 --effort high` (default `sonnet55`, `medium`) |
| `--hallways` | a run that allows hallways: the agents get `house/prompt_template_hallways.txt` and the server lets their scripts place hallways |
| `--max-tries` | tries per step before the chain stops |

Every script sent is saved in the data folder as one JSON record (`run_0001.json`), with a copy to read in a text
editor (`run_0001.txt`: the script and the drawing). The agents' raw replies are in `replies/`. Each record also holds
the token usage and dollar cost of the agent call that wrote it (`agent_usage`); failed tries count, because they cost
tokens too.

## 70-to-100-room chains

`house.run_100_rooms` runs the separate 15×15 experiment ([The 70-to-100-room runs](study-design.md#the-70-to-100-room-runs)). Its records
use the same JSON shape as other runs: script, request, layout, validity, scores and agent metadata. Claude records
include token usage and dollar cost. Copilot CLI records use `agent_cli`, `agent_version`, `model`, `model_label`,
and `effort`; raw Copilot usage events are kept under `agent_metadata.copilot_usage_events`. When Copilot does not
report token counts or a dollar cost, those `agent_usage` values are null rather than estimated.
Each record also saves the time spent waiting for that call as `call_duration_ms` and the chain's elapsed wall time
as `chain_elapsed_ms`, with `chain_started_at` identifying its start. If a chain resumes from older records without
timing metadata, its elapsed time is marked estimated.

The no-hallways run has twelve chains, three per seed house, all in one folder: chains 1–4 and 9–12 use Sonnet 5.5,
chains 5–8 use GPT-6 Luna. Chain number and seed-house number are separate: chain 5 and chain 9 both start from seed
house 1. Records are told apart by the label prefix (`sonnet55`, `gpt6luna`) and the `model` field, so filter by
model before analysing:

```
.venv/bin/python -m house.run_100_rooms --runs runs_100_rooms_no_hallways --no-hallways --house 1 --chain 9
.venv/bin/python -m house.run_100_rooms --agent copilot --model gpt-6-luna --effort medium \
  --no-hallways --house 1 --chain 5
```

Houses 2–4 take chains 10–12 (Sonnet 5.5) and 6–8 (GPT-6 Luna). Report the two models separately. Copilot billing is reported by the CLI in AI credits or
premium requests, depending on the account, and is not converted into Claude-style dollar costs.

The reorganising run has one Sonnet 5.5 chain per seed house:

```
.venv/bin/python -m house.run_100_rooms --runs runs_100_rooms_refactor --refactor [--house 1]
```

The cost run is the reorganising run with every command priced. It has four Sonnet 5.5 chains, 5–8, one per seed
house, and two DeepSeek chains, 1 and 3, on seed houses 1 and 3:

```
.venv/bin/python -m house.run_100_rooms --refactor --cost --effort medium --house 1 --chain 5
.venv/bin/python -m house.run_100_rooms --refactor --cost --agent deepseek --effort low --house 1 --chain 1
```

Houses 2–4 take Sonnet chains 6–8; house 3 takes DeepSeek chain 3.

The cost-only run is the hallway run with every command priced. It has two Sonnet 5.5 chains, 5 and 7, and two
DeepSeek chains, 1 and 3, on seed houses 1 and 3:

```
.venv/bin/python -m house.run_100_rooms --cost --effort medium --house 1 --chain 5
.venv/bin/python -m house.run_100_rooms --cost --agent deepseek --effort low --house 1 --chain 1
```

House 3 takes Sonnet chain 7 and DeepSeek chain 3.

The DeepSeek chains use the standalone DeepSeek adapter at low thinking. It posts the house prompt directly to
DeepSeek's Anthropic-compatible API with thinking enabled at low effort, and its records carry
`agent_cli: deepseek-api` and `effort: low`. It uses `DEEPSEEK_API_KEY` (or `ANTHROPIC_AUTH_TOKEN`) and
`DEEPSEEK_BASE_URL` (or `ANTHROPIC_BASE_URL`, default `https://api.deepseek.com/anthropic`). The hallway run and the
reorganising run each have DeepSeek chains 5 and 7, on seed houses 1 and 3:

```
.venv/bin/python -m house.run_100_rooms --agent deepseek --effort low --house 1 --chain 5
.venv/bin/python -m house.run_100_rooms --runs runs_100_rooms_refactor --refactor \
  --agent deepseek --effort low --house 1 --chain 5
```

The Opus 5.5 chains run through Claude Code at medium effort: chain 9 on seed house 1 in the hallway, reorganising,
cost and cost-only runs, and chain 10 on seed house 2 in the hallway run:

```
.venv/bin/python -m house.run_100_rooms --runs runs_100_rooms --model opus55 --effort medium --house 1 --chain 9
.venv/bin/python -m house.run_100_rooms --runs runs_100_rooms_refactor --refactor --model opus55 --effort medium --house 1 --chain 9
.venv/bin/python -m house.run_100_rooms --refactor --cost --model opus55 --effort medium --house 1 --chain 9
.venv/bin/python -m house.run_100_rooms --runs runs_100_rooms_cost --cost --model opus55 --effort medium --house 1 --chain 9
```

House 2 in the hallway run takes chain 10.

## Running by hand

The same chain can be run with any agent, one step at a time, in the order A to J:

```
.venv/bin/python -m house.experiment --runs runs_new prompt --chain 1 --step B              # paste into a fresh agent
.venv/bin/python -m house.experiment --runs runs_new send   --chain 1 --step B reply.txt    # its reply, unedited
```

`send` puts the right starting house on the server, sends the script with the request it answers (so the server can
check the requested rooms) and prints the outcome. On `valid.` go to the next step; on `script REJECTED` or
`house INVALID` run the same step again with a fresh agent. Add `--model`, `--effort` and `--hallways` to both
commands as needed. Records made by hand have no token usage.

## The runs in the report

Every run used Claude Sonnet 5.5 in six chains. Its analysis plan was written before its first agent call and has not
been changed since.

| Run | Settings | Code | Analysis plan | Data |
|---|---|---|---|---|
| 1. First run | hallways, nothing costs, medium effort | `0f79745` | `paper/ANALYSIS_PLAN.md` | `runs/` |
| 2. No hallways | no hallways, nothing costs, medium effort | `dd9ab04` | `paper/ANALYSIS_PLAN_no_hallways.md` | `runs_no_hallways/` |
| 3. Low effort | no hallways, nothing costs, low effort | `dd9ab04` | `paper/ANALYSIS_PLAN_no_hallways_low.md` | `runs_no_hallways_low/` |
| 4. Cost without hallways | no hallways, every change has a price, medium effort | `25e3cef` | `paper/ANALYSIS_PLAN_cost.md` | `runs_cost/` |
| 5. Cost with hallways, run twice | hallways, every change has a price, medium effort | `25e3cef` | `paper/ANALYSIS_PLAN_cost_hallways.md` | `runs_cost_hallways/`, `runs_cost_hallways_2/` |

The code on `main` is the code of the cost runs. The report's Reproducibility section gives the commands to repeat
each run at its commit.

## Results

```
.venv/bin/python -m house.experiment --runs runs_new report    # one data folder
.venv/bin/python paper/build_report.py                         # REPORT.md, from every data folder
```

`report` prints, per chain and averaged over chains, the tries and the four scores of every step with the cost of
its script, the token usage, and drawings of A, H, I and J side by side.

`paper/build_report.py` fills `paper/REPORT.template.md` with numbers, tables and drawings computed from the saved
records, following the analysis plans. Every number in `REPORT.md` comes from there; edit the template, not the
report.

## Other tools

```
.venv/bin/python -m house.prompt "add: bathroom"                       # the prompt for the server's current layout
.venv/bin/python -m house.prompt "build: living room, kitchen, bedroom x2, bathroom" --empty
.venv/bin/python -m house.render examples/example_house.txt examples/chain_house.txt   # drawings side by side
curl localhost:8000/layout                                             # the server's current layout
curl -X PUT --data-binary @house.txt localhost:8000/layout             # load a layout (an empty body resets)
curl --data-binary @script.txt "localhost:8000/script?label=test"      # send a script
```
