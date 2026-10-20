# House DSL

Design: `HOUSE_DSL.md`. Python 3.9+, tests with pytest (`.venv` holds Python 3.12 and pytest).

```
.venv/bin/python -m pytest -q                                  # tests
.venv/bin/python -m house.server [--port 8000] [--runs runs] [--layout FILE]
curl localhost:8000/layout                                     # current layout
curl --data-binary @script.txt "localhost:8000/script?label=claude-patch-1"
curl -X PUT --data-binary @house.txt localhost:8000/layout     # load a layout (empty body resets)
.venv/bin/python -m house.prompt "add: bathroom"               # prompt for a fresh agent (layout from the server)
.venv/bin/python -m house.prompt "build: living room, kitchen, bedroom x2, bathroom" --empty
.venv/bin/python -m house.render examples/example_house.txt examples/chain_house.txt   # side by side
```

Running the experiment: see `EXPERIMENT.md`.

Modules: `model` (grid, cells, edges, rooms), `layout_format` (text format), `commands` (syntax), `interpreter`
(run a script), `rules` (hard rules), `scores` (four scores), `render` (ASCII), `server`, `recorder` (saved runs),
`prompt`, `experiment` (the chain of agents A to E, and the report).
