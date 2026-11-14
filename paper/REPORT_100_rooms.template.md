# Patching versus planning in houses of 70 to 100 rooms

## Abstract

Does a design patched for one new requirement at a time end up worse than one that takes all the remaining
requirements in one go? On a small grid it did, but only when every change had a cost and hallways could be built.
This report asks the same question with houses big enough that starting over is no longer easy: houses of 70 rooms
grown to 100, either one room at a time or all the remaining rooms at once. There are four starting houses and five
runs: with hallways, without hallways, with a request to reorganise the house before adding to it, with that request
and a cost on every command, and with the cost alone.

Claude Sonnet 5.5 refactored only when asked to reorganise. If every command also had a cost, it stopped refactoring
and only added rooms to the house it was given, the cheapest way. Asked to reorganise, DeepSeek refactored far more
than Sonnet, both step by step and all at once. A cost on every command made it refactor less, but DeepSeek did not
stop refactoring. Claude Opus 5.5, left to itself, refactored once at the start and then built on what it had. Asked
to reorganise, it kept refactoring as the house grew. With a cost on every command as well, it went back to
refactoring once. With the cost and no request to reorganise, it did not refactor at all. GPT-6 Luna, in the run
without hallways, refactored the badly grown houses without being asked. Refactoring was not the same as improving.

In most runs it made no clear difference whether the rooms were added one at a time or all at once. The exception was
the run with a cost and no request to reorganise, the same conditions in which the small grid showed a difference. In
that run, Opus's house and one of DeepSeek's two ended with more corridor rooms when built one room at a time than when
built all at once. Sonnet's houses did not.

[Watch the videos](viewer/videos/watch.md)

## 1. Question

The first report (`REPORT.md`) used a 5×5 grid on which building and demolishing were free. On that grid, adding rooms
one at a time never ended worse than planning them all together, and the agents showed no built-in habit of making
only small, local changes. But a house of up to 11 rooms is easy to redesign. This report asks the question again with
houses of 70 rooms grown to 100 on a 15×15 grid, at first with building and demolishing still free:

- Does adding the rooms one at a time end worse than adding all the remaining rooms at once to the same house?
- Does it matter which house the agents start from: one that grew on a tight budget, or one that grew with no thought
  of cost?
- When no hallway can be built, do the agents redesign the house, as they did on the small grid, or does its size stop
  them?

The later runs ask two more things. First, if the agents are asked to reorganise the house before adding to it, do
they refactor? Second, on the small grid, with hallways and a cost on every command, adding rooms one at a time did
end worse. Does it here too, with and without the request to reorganise?

## 2. How the runs worked

The full design is in [the study design](docs/study-design.md#the-70-to-100-room-runs). In short:

* **Four seed houses of 70 rooms**, made in code. Houses 1 and 2, the budget houses, grew on a tight budget, the way
  the agents of the priced 5×5 runs added rooms. Houses 3 and 4, the planned houses, grew with no thought of cost,
  each time by the change that gave the best scores. Out of 24 candidates, these four were the houses whose outcome
  depended most on how they were extended.
* **Chains.** A chain is one model growing one seed house from 70 to 100 rooms in two ways side by side. Step by step:
  30 agents in a row, each adding one room to the house the one before it left. All at once: from the house as it
  stood after each of steps 0 to 28, one agent adds every room still missing. That makes 59 agents per chain. Each
  agent starts fresh, gets no feedback, and hands in one script of commands. In the tables, "after step 30" is the
  house built step by step, and "all at once from step 0" is the house built all at once from the seed.
* **Five runs.** In run 1 hallways can be built. In run 2 no hallway can be built; the hallways the seed houses
  already have can be used or removed. In run 3 hallways can be built, and every agent is asked to reorganise the
  house before adding to it. Run 4 is run 3 with a cost on every command, as in the priced runs on the small grid:
  building or removing a room costs 4, a door or a window 1, and the agent is told that its work is also judged by the
  total cost of its script. Run 5 is run 1 with the same cost, without the request to reorganise.
* **Models.**
  - Claude Sonnet 5.5 at medium effort, through Claude Code: four chains in run 1, one per seed house (Claude Code
    {{r1_versions}}); eight in run 2, two per seed house ({{r2_s_versions}}); four in run 3 ({{r3_s_versions}}); four
    in run 4 ({{r4_s_versions}}); and two in run 5, houses 1 and 3 ({{r5_s_versions}}).
  - Claude Opus 5.5 at medium effort, through Claude Code: two chains in run 1, houses 1 and 2, and one in each of
    runs 3, 4 and 5, house 1 ({{o_versions}}).
  - DeepSeek flash (DeepSeek-V4.1-Flash-1017) at low thinking, through a separate adapter (version
    {{r3_adapter_version}}): two chains, houses 1 and 3, in each of runs 1, 3, 4 and 5.
  - GPT-6 Luna at medium effort: four chains in run 2, one per seed house ({{r2_l_version}}).

  The models are reported separately.

The runs describe what the agents did; they do not test the statistical significance of the results. Every house gets
four scores: corridor rooms, privacy order, walking distance and compactness. Lower is better for each, and [the study
design](docs/study-design.md#quality-score-fitness-functions) defines them. An agent refactored when it removed or
replaced 10% or more of the house it was given.

## 3. Run 1: hallways can be built

### 3.1 The houses at the end

Sonnet 5.5:

{{r1_final}}

DeepSeek flash:

{{r1_final_deepseek}}

Opus 5.5:

{{r1_final_opus}}

We expected the house built step by step to end no worse than the one built all at once from the seed, as on the small
grid. For Sonnet it ended worse on one score, corridor rooms: in every house, the house built step by step had more
rooms that people must walk through, while the one built all at once kept about as many as the seed had. On the other
scores, building step by step mostly did better: its houses were shorter to walk in all four houses and more compact
in {{r1_compact_better}} of the four, and privacy order was the same either way. Built step by step or all at once
from the seed, DeepSeek's and Opus's houses ended with no corridor rooms, or one at most. Every step's scores are in
Appendix A.

### 3.2 What the agents changed

{{r1_changes}}

Sonnet did not refactor. Working step by step it never removed more than one room, and working all at once it never
removed more than {{r1_all_removed_most}} of the house. The two ways differed in what they added: a step added
{{r1_step_hall}} hallways on average, an all-at-once agent {{r1_all_hall}}.

DeepSeek refactored, mostly when it saw all the rooms at once. Its steps removed rooms in {{r1_d_step_removed}} of
{{r1_d_step_calls}} cases, but only one step in each house refactored, removing up to {{r1_d_step_most}} of it. Its
all-at-once agents refactored in {{r1_d_all_big}} of the 29 in each house, the first one included ({{r1_d_all_first}}
of the house). It added {{r1_d_step_hall}} hallways per step and {{r1_d_all_hall}} per all-at-once agent.

Opus refactored once, at the start. In each house its first step and its first all-at-once agent each removed between
65% and 77% of the house, and no later agent refactored. It added {{r1_o_step_hall}} hallways per step and
{{r1_o_all_hall}} per all-at-once agent.

### 3.3 Why it happens

Working all at once, Sonnet saw every missing room, so it could lay out hallways to serve them all. It built them as a
wing behind the house and hung the new rooms on it. Almost none of the new rooms ended up on anyone's way, so the
number of corridor rooms stayed as in the seed. But the wing sits beyond the old house, so its rooms are far from
everything else, and the walks got longer. Working step by step, Sonnet saw one room, and a hallway for one room is
rarely worth it. So it mostly gave the new room a door into a room already there, and each time that room was a
bedroom or bathroom at a dead end, it became a room people walk through. Over 30 steps those added up.

DeepSeek did not keep the house it was given. In each house one step laid out more than half the house again, and some
of its all-at-once agents did the same. In the end, none of its houses had a kitchen, bedroom or bathroom that people
walk through.

Opus laid the house out again with its first agent of each kind, then kept that layout and added each new room to it.

### 3.4 Failed tries and cost

{{r1_tries}}

When an agent failed, a fresh one tried again, and every step was done within three tries, so every chain has all 59
houses. The Sonnet and Opus costs are Claude Code's figures; the DeepSeek costs are worked out from DeepSeek's
published prices.

## 4. Run 2: no hallway can be built

### 4.1 The houses at the end

Sonnet 5.5:

{{r2_final_sonnet}}

GPT-6 Luna:

{{r2_final_luna}}

The house built all at once from {{r2_missing}} is missing: all three tries were rejected, and the chain carried on
without it. Every step's scores are in Appendix B.

In the {{r2_s_chains}} Sonnet chains, neither way of building came out ahead. The house built step by step had fewer
corridor rooms than the one built all at once from the seed in {{r2_s_corr_lower}} chains, and more in
{{r2_s_corr_higher}}. It was shorter to walk in {{r2_s_walk_lower}} chains, and longer in {{r2_s_walk_higher}}. In the
{{r2_l_chains}} GPT-6 Luna chains, the house built step by step had more corridor rooms in all {{r2_l_corr_higher}}.
It was shorter to walk in {{r2_l_walk_lower}}, and longer in {{r2_l_walk_higher}}.

Every chain of both models ended with more corridor rooms than its seed house, and on every seed house GPT-6 Luna
ended with more than both Sonnet chains. GPT-6 Luna's houses were shorter to walk than Sonnet's on the two budget
houses, and longer on the two planned houses.

### 4.2 What the agents changed

{{r2_changes}}

Sonnet changed almost nothing it was given. No all-at-once agent removed a room. Of {{r2_sonnet_steps}} steps,
{{r2_sonnet_removing_steps}} removed one room each, all in the planned houses: {{r2_sonnet_gone_hallways}} a seed
hallway and one a bathroom. No step added more than one door beyond those of its new room.

GPT-6 Luna changed the houses in two ways. First, it opened up the house with extra doors. In {{r2_luna_rewired}} of
its {{r2_luna_calls}} agents, {{r2_luna_rewired_all}} of them all at once, it added ten or more doors beyond those its
new rooms needed, and {{r2_luna_rewired_kept}} of those agents removed no room at all. The biggest was
{{r2_luna_big_where}}: it added {{r2_luna_big_doors}} doors and raised corridor rooms from {{r2_luna_big_before}} to
{{r2_luna_big_after}}. Second, {{r2_luna_rebuilt}} agents removed a quarter of the house or more, all in the budget
houses, and {{r2_luna_rebuilt_steps}} of them was a step. In each budget house step {{r2_luna_redesign_step}}
redesigned the house, and the later steps built on that design. Every agent that opened up or rebuilt a house raised
its corridor rooms.

### 4.3 Why it happens

Without hallways, a new room can only be reached through a room already there, so every new room risks turning another
room into one people walk through. An agent working all at once can no longer build a hallway wing for the new rooms.
So it attaches them one after another, just as the step-by-step agents do, and neither way ends ahead. Sonnet did
exactly that and nothing more: it took the house as given and attached rooms to it. The budget houses started with
many corridor rooms, kept them, and gained more.

GPT-6 Luna did not take the house as given. It opened extra doors between neighbouring rooms, and in the budget houses
it took large parts apart and laid them out again, heading towards a house in which every room opens onto the rooms
around it. Such a house is short to walk, because there is a direct way almost everywhere. But the direct way runs
through bedrooms and bathrooms rather than hallways, so more of them end up being walked through. GPT-6 Luna
redesigned houses mostly when it saw all the rooms at once, but a single step was enough to redesign a budget house.
So whether a house was redesigned depended on the model, not on the order in which the rooms arrived.

### 4.4 Failed tries and cost

{{r2_tries}}

Copilot CLI does not report tokens or cost for GPT-6 Luna.

## 5. Run 3: reorganise first

### 5.1 The houses at the end

Sonnet 5.5:

{{r3_final_sonnet}}

DeepSeek flash:

{{r3_final_deepseek}}

Opus 5.5:

{{r3_final_opus}}

The house built all at once from {{r3_missing}} is missing: all three tries were rejected, and the chain carried on
without it. Every step's scores are in Appendix C.

We expected the house built step by step to end no worse than the one built all at once from the seed, as in the free
5×5 runs, and that mostly held. In the {{r3_chains}} Sonnet and DeepSeek chains, both ways ended with the same number
of corridor rooms in {{r3_corr_same}} chains; building step by step gave fewer in {{r3_corr_lower}} and more in
{{r3_corr_higher}}. Building step by step also gave a shorter walk in {{r3_walk_lower}} chains, and a longer one in
{{r3_walk_higher}}. The big change in this run was not in the scores but in what the agents did: they now rebuilt the
house.

The request changed what the agents did. The first steps removed most of the seed house and rebuilt it, and
{{r3_step30_zero}} of the six houses built step by step ended with no corridor rooms. One all-at-once agent working
from the seed did not rebuild: it kept the seed house, added a wing, and so kept the seed's corridor rooms. Of the six
houses built all at once from the seed, {{r3_all00_zero}} ended with none. Since both kinds of agent rebuilt, corridor
rooms no longer told the two ways of building apart. Only the length of the walk still differed. Opus's houses all
ended with no corridor rooms.

### 5.2 What the agents changed

{{r3_changes}}

The table adds up every chain of a model: four seed houses for Sonnet, two for DeepSeek and one for Opus, so its rows
do not compare like with like. It also counts every agent that removed a room, even a single one, while an agent
refactored only when it removed or replaced 10% or more of the house.

House 1 is the one all three models built, and there the difference is clear. Sonnet refactored at the start and then
mostly kept what it had: {{r3_s1_steps_big}} step refactored, the first, and {{r3_s1_all_big}} all-at-once agents, the
first and the one from step 21. DeepSeek refactored in {{r3_d1_steps_big}} of its 30 steps and {{r3_d1_all_big}} of
its all-at-once agents. Opus came in between: {{r3_o_steps_big}} of its 30 steps and {{r3_o_all_big}} of its 29
all-at-once agents refactored.

On the other seed houses Sonnet's steps also refactored mostly at the start, with one exception: in house 4 the first
step changed only 11% of the house, and step 15 laid out 81% of it again. Two later steps, in houses 2 and 3, changed
just over 10%: 13% and 11%.

### 5.3 Why it happens

The request asked every agent to make the house simpler before adding to it. Sonnet's agents did: its first steps
removed {{r3_s_first}} rooms in the four chains, and its all-at-once agents removed rooms too. DeepSeek removed more:
its first steps removed {{r3_d_first}} rooms, and one of its steps removed {{r3_d_step_removed_most}} of the house,
against at most {{r3_s_step_removed_most}} for a Sonnet step. Rebuilding more did not make the houses shorter to walk:
DeepSeek's houses were longer to walk than Sonnet's. In one DeepSeek chain, the all-at-once agent working from the
seed kept the house and added a wing instead of rebuilding; the step that followed rebuilt it. The request is what
made the agents rebuild, and where it failed, it failed for a single agent, not for a model. Redesigning was not the
same as improving.

Opus reorganised at intervals: each step that laid the house out again (steps {{r3_o_big_steps}}) was followed by
steps that changed less than 10% of it.

### 5.4 Failed tries and cost

{{r3_tries}}

The Sonnet and Opus costs are Claude Code's figures; the DeepSeek costs are worked out from DeepSeek's published
prices. In run 3, building and demolishing cost nothing.

## 6. Run 4: reorganise, with cost

### 6.1 The houses at the end

Sonnet 5.5:

{{r4_final_sonnet}}

DeepSeek flash:

{{r4_final_deepseek}}

Opus 5.5:

{{r4_final_opus}}

Every step's scores are in Appendix D.

In the Sonnet chains, building step by step mostly ended with more corridor rooms but a shorter walk. The house built
step by step had more corridor rooms than the one built all at once from the seed in {{r4_s_corr_higher}} of the four
houses, and fewer in {{r4_s_corr_lower}}. It was shorter to walk in {{r4_s_walk_lower}}, and longer in
{{r4_s_walk_higher}}. DeepSeek's houses, built either way, ended with no corridor rooms, and those built step by step
were longer to walk. Opus's houses all ended with no corridor rooms.

### 6.2 What the agents changed

{{r4_changes}}

With a cost on every command, Sonnet did not refactor, even though every agent was asked to reorganise. Only
{{r4_s_step_removed}} of its {{r4_s_step_calls}} steps removed a room, and {{r4_s_all_removed}} of its
{{r4_s_all_calls}} all-at-once agents. No agent removed more than {{r4_s_most}} of the house. In run 3, without the
cost, one Sonnet agent removed {{r3_s_most}}.

DeepSeek still refactored. Its first step removed {{r4_d_first}} of the house, and one agent up to {{r4_d_most}}. It
refactored in {{r4_d_steps_big}} of the 30 steps in each house, against {{r3_d_steps_big}} in run 3, and in
{{r4_d_all_big}} of the 29 all-at-once agents.

Opus refactored once: its first step removed 39% of the house and its first all-at-once agent 36%, and no later agent
refactored. In run 3, without the cost, {{r3_o_steps_big}} of its steps did.

### 6.3 Why it happens

The prompt asks for two things: reorganise the house, and keep the total cost of the script low. Refactoring means
removing rooms and building them again, and every one of those commands costs something. Sonnet chose the cost: its
median step cost {{r4_s_step_cost}}, the new room and one door, and none cost more than {{r4_s_step_cost_max}}. It
only added to the house, as in run 1, where nobody asked it to reorganise. DeepSeek chose to reorganise: its median
step cost {{r4_d_step_cost}}, and one cost {{r4_d_step_cost_max}}. The cost made it refactor less often than in run 3,
but did not stop it. Opus kept its first refactoring and dropped the later ones it made in run 3.

### 6.4 Failed tries and cost

{{r4_tries}}

The Sonnet and Opus costs are Claude Code's figures; the DeepSeek costs are worked out from DeepSeek's published
prices.

## 7. Run 5: cost, no reorganise

### 7.1 The houses at the end

Sonnet 5.5:

{{r5_final_sonnet}}

DeepSeek flash:

{{r5_final_deepseek}}

Opus 5.5:

{{r5_final_opus}}

Every step's scores are in Appendix E.

On the small grid, with hallways, a cost and no request to reorganise, houses built step by step ended worse than
planned ones. Run 5 sets the same conditions at 100 rooms. In Sonnet's chains the two ways ended about level: the house
built step by step and the one built all at once from the seed ended with corridor rooms {{r5_s_pairs}}, and with
walking distances within 0.15 of each other. In DeepSeek's chains, the house built step by step had fewer corridor
rooms in house 1 and more in house 3. Opus's house built step by step ended with 65 corridor rooms, against 41 and 53
for its houses built all at once from steps 0 and 15.

### 7.2 What the agents changed

{{r5_changes}}

No model refactored. Sonnet's steps removed no room, and {{r5_s_all_removed}} of its {{r5_s_all_calls}} all-at-once
agents removed one each. No DeepSeek agent removed more than one room. Opus's steps removed no room, and no
all-at-once agent removed more than two.

### 7.3 Why it happens

When Sonnet added one room, it always did it the cheapest way: it built the room and gave it one door into a room next
to it. That cost 5 every time, 4 for the room and 1 for the door, just as on the small grid. What changed from the
small grid was the agent that added all the rooms at once. Without the cost, in run 1, it built a wing of hallways
behind the house, {{r1_all_hall}} hallways each time. With the cost it built only {{r5_s_all_hall}}, and its houses
gained corridor rooms: {{r5_s_all00_corr}}. Both kinds of agent only added to the house they were given, so neither
way of working ended ahead.

Opus, adding one room at a time, never built a hallway. Each new room got a door into a room already there, and the
house ended with 65 corridor rooms, up from 42. When it added all the rooms at once it still built hallways,
{{r5_o_all_hall}} a time, and those houses ended with fewer corridor rooms.

### 7.4 Failed tries and cost

{{r5_tries}}

The Sonnet and Opus costs are Claude Code's figures; the DeepSeek costs are worked out from DeepSeek's published
prices.

## 8. Limitations

Each run has one chain per seed house and model, except Sonnet in run 2, which has two. DeepSeek covers only houses 1
and 3, and so does Sonnet in run 5. Opus covers house 1, plus house 2 in run 1, and did not take part in run 2. Each
model ran at one effort level, and GPT-6 Luna in one run only. DeepSeek ran through a separate adapter with a plain
prompt and low thinking, not through Claude Code, so its chains cannot be compared with Sonnet's point by point.
DeepSeek is also much slower than Sonnet: {{call_s_deepseek}} seconds per agent on average against {{call_s_sonnet}},
and {{chain_h_deepseek}} hours per chain against {{chain_h_sonnet}}. We ran it at low thinking because at high effort
it was slower still. Claude Code changed version between the runs and within run 2 (Section 2). A single chain shows
what an agent did, not how often it would do it.

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
start, then keeps what it built and adds the new rooms on top. Asked to reorganise, it refactors again and again as
the house grows, more often than Sonnet and less often than DeepSeek, unless every command has a cost. Only cost
without a request to reorganise stops that first refactoring, and in that case the incremental house ended with more
corridor rooms than the all-at-once houses. On house 1 neither Sonnet nor DeepSeek did this.
- Run 1 (no cost, no reorganise), houses 1 and 2: the first step refactored 65% and 77% of the house, and the first
  all-at-once call 67% and 67%. No later call refactored 10% or more. All its final houses have 0 or 1 corridor rooms.
- Run 3 (no cost, reorganise), house 1: 9 of 30 steps and 19 of 29 all-at-once calls refactored 10% or more. All its
  final houses have 0 corridor rooms.
- Run 4 (cost, reorganise), house 1: the first step refactored 39% and the first all-at-once call 36%. No later call
  refactored 10% or more. All its final houses have 0 corridor rooms.
- Run 5 (cost, no reorganise), house 1: no call refactored more than 2.4%. The incremental house ended with 65 corridor
  rooms against 41 and 53 for the all-at-once houses.

4. The 5×5 result. On the 5×5 grid, with hallways, cost and no reorganise, houses built step by step ended worse than
planned ones. Run 5 has the same conditions at 100 rooms. With Sonnet the two houses showed no difference. With Opus,
and with DeepSeek in one of its two houses, the house built step by step ended with more corridor rooms than the
houses built all at once, as on the 5×5 grid. These are single chains: they show that the 5×5 result can happen at 100
rooms, not how often it does.

## Appendix A. Run 1, step by step

Each row is one way of building in one chain: the house after the step, or the house built all at once from the house
after that step. Step 0 of "after the step" is the seed house. All-at-once agents start from steps 0 to 28, so step 30
has none.

{{r1_along}}

## Appendix B. Run 2, step by step

As in Appendix A.

{{r2_along}}

## Appendix C. Run 3, step by step

As in Appendix A.

{{r3_along}}

## Appendix D. Run 4, step by step

As in Appendix A.

{{r4_along}}

## Appendix E. Run 5, step by step

As in Appendix A.

{{r5_along}}

## Reproducibility

The data are in `runs_100_rooms/` (run 1), `runs_100_rooms_no_hallways/` (run 2), `runs_100_rooms_refactor/` (run 3),
`runs_100_rooms_refactor_cost/` (run 4) and `runs_100_rooms_cost/` (run 5). Every agent's work is one JSON record with
its script, the house it produced, the house's scores and the agent's token usage. The seed houses and the code that
made them are in `runs_100_rooms/seeds/`. The chains were run with `python -m house.run_100_rooms` as described in
[running the experiment](docs/running-the-experiment.md#70-to-100-room-chains); the DeepSeek chains used the separate
adapter. This report is generated by `python paper/build_report_100_rooms.py` from
`paper/REPORT_100_rooms.template.md`.
