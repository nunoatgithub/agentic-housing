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
