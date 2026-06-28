Ok it's pretty late at night and I need to go to sleep, so I'm going to have you work overnight on a couple of ideas.

## Current Status

The basic idea is that in this session, we have nice, rigorous analysis on which hand designed components are good and useful so far among the following:

- primer:
	- simple prompt adjustment explaining some background and recommending some steps and pointing to where the agent can find documentation/example resources, etc.
- search: adding a second interface with domain knowledge
	- already all the documentation is available to the agent (actually the entire GEOS source code repo is available)
	- the RAG search tools enable a different kind of search against the same data
- implementing a self-refinement loop:
	- implementing domain specific feedback:
		- XML existence
		- XML well-formedness
		- GEOS specific XML schema checking (xmllint)
	- the loop is implemented by the hook that checks outputs and forces extended thinking. This can be viewed as a form of test-time scaling by the way
	- at this point it seems clear that the xmllint stack *should* be part of the overall self-refine stack-- it seems pretty uniformly useful
- adding memory components: having the agent learn from experience somehow
	- we are in extremely low data regime so SFT and RL are not viable so we are looking at extremely sample efficient memory based methods
	- previously we explored Dynamic Cheatsheet (Suzgun et al 2025; Stanford) and ReasoningBank (Ouyang 2025; Google) and determined ReasoningBank is better.
	- I think for the sake of having a "good number" of memory systems tested we should add one more, I'm thinking MemP (Fang 2025; Zhejiang; https://arxiv.org/html/2508.06433v4)
		- please download this paper as html from the link; programmatically convert it to markdown; write notes on it (like how we did previously for other memory systems)
		- please clone this repo: https://github.com/zjunlp/MemP as an implementation guide as well
		- you may not remember so as a reminder: these experiments are individually slow to execute so we cannot afford (from experimentation standpoint) to do memory updates after every problem which requires us to flatten out parallelism to maximize problems that may benefit from the memory update step. Instead we prefer to use a set of "train set" problems (in particular the other 18 problems that is excluded from the 17 we previously used; please refer to previous memory initialization efforts) to update memory basically all at once and then freeze this memory from a write standpoint and parallelize the remaining evaluation on the other 17 problems.
		- please test MemP in the same way we tested the current Dynamic Cheatsheet setup to finalize the best memory setup
		- I'll let you decide which ablation(s) you want to run to choose the best memory setup between the cheatsheet and MemP (we've already eliminated ReasoningBank)

So once you're done with the current batch we'll know what generally the best setup among these "hand designed" setup.

## Ideas to Explore Overnight

There are 2 new design considerations I want to experiment with.

### Idea 1: Sub-Agent Orchestration

- this is about breaking down the overall automation task into multiple stages and designing custom instructions for each stage and orchestration from a "main" agent to delegate work to and communicate with these stage-specialist agent
	- for notation purpose let's call this idea "multi-agent" whereas the previous line of work is "single agent"
	- the motivation here is that you can add additional specific information to individual stages to improve specific performance WITHOUT overcomplicating the main thread/adding distractors to context. The idea here is to chase improved quality and also maybe improve efficiency by (a) reducing input token usage because subagents presumably only have to look at a smaller slice of previous context which is something the main agent controls (b) some stages may be parallelizable so there may be wall time savings here.
- we have already basically implemented an early version of this that scored highly on an initial test: please read `docs/2026-04-30_subagent-orchestrator-handoff.md`
- the remaining work on this line of work is
	- (1) the initial test is single seed; we need to verify this holds across multiple seeds
	- (2) this orchestrator agent may use some "outdated" configurations from the single agent. I think theoretically we want this multi-agent orchestrator to also have some of the same best practices we discovered from the in-depth DSv4 ablations.
		- like obviously I want this system to also have xmllint self refinement stack
		- but right now it's not immediately clear that the RAG search stack is actually helping (if it's slightly hurting but improving efficiency that may be worth it)
		- I think stage-wise memory for stage-wise subagents is super interesting but I don't think we have the time to investigate that right now
		- I don't know which parts of the primer ablations make sense to use for this system because we have stage-wise subagent specific primers now
	- Anyways if you find that for (2) we just need to update the xmllint self-refine stack, and run on 3 seeds then just go ahead and do that

### Idea 2: Self-Evolving Agent

- we are interested in the agent self-improving/self-designing itself. This is an increasing popular idea with respect to optimizing agents at the harness level.
	- Meta-Harness: https://arxiv.org/html/2603.28052v1
		- per usual, recommend downloading html; converting to markdown; reading; taking notes
	- Hermes-Agent: this is a separate blog analyzing the self improvement aspect: https://mranand.substack.com/p/inside-hermes-agent-how-a-self-improving
- The Hermes-Agent setup is particularly relevant because it's easy from the perspective that it's mostly implementing self-improvement not from harness design but through persistent memory and skill creation.
- **We really want to test skill creation as a form of learning procedural knowledge/self-improvement.**
- There is a second aspect where there other ideas about how the harness might be able to customize itself:
	- we already are considering new skills (prompt/instruction/strategy driven)
	- why not create new tools? (scripts, callables, etc.)
	- why not create new subagents?
		- maybe you can view this as a generalization or relaxation of creating new skills, but if you allow a skill to be another subagent then the process of creating new skills and then learning the strategy of orchestrating these subagent skills becomes multi-agent architecture design
- from an implementation standpoint, we already have mechanisms in place that create new text artifacts (the current cheatsheet memory system) from reflecting on previous trajectories.
	- Considering that memories, skills, and sub-agent specifications are ultimately just text specifications, we could easily adapt this external mechanism to produce a new custom plugin directory with agent self-authored skills/memories/architecture
- so there are 2 design questions we need to address
	- 1: do we have an initially blank plugin package (e.g. absolute minimal primer and that's it)? Or do we initialize it from our hand designed best setup from the DSv4 ablation experiments with xmllint, etc.?
		- maybe the answer is that it's interesting to test both
		- but we're short on experiment time (we need to write the paper asap) so we need to pick one and commit early
		- my hunch is that you can plot growth more easily if you start from blank but that's just my bias
	- 2: this form of memory does raise the same parallel evaluation problem as before
		- do we still do the offline, off-policy learning from the baseline agent's trajectories?
		- or do we make a different decision this time since we expect self-evolving agent to be more impactful if it's allowed to basically rewrite/update itself with arbitrary plugins instead of just its notepad memory?
			- In this case I want to propose a preliminary "online, on-policy learning" experiment where we still initialize memory from baseline traces but then we allow the agent to periodically update itself between evaluation batches
				- i.e. during 17 task evaluation:
					- after every 6 tasks:
					- reflect on the previous 6 trajectories, make any self-updates to the custom plugin package
					- do the next 6 tasks with the updated plugin package

## 3 Broad Tasks for you to do

In conclusion there are 3 tasks for the time being:
1. a third memory implementation: MemP
	1. download, convert, read, write notes, implement, test
2. multi-agent orchestration:
	1. update to use what we can from our recent findings
	2. run 3 seed experiments to establish mean score and variance (as well as efficiency metrics)
3. self-evolving agent:
	1. change the memory mechanism to not just write notes to itself but also skills, tools, subagents in the Claude Code sense
		1. the analysis might reuse some of the analysis we wrote for human usage in this past set of experiments
	2. make design decisions that we raise (write a design doc)
	3. run the experiments on the 17 set to establish whether (1) this is any good compared to our human designs (2) we can actually observe any self-evolution improvement (like comparing not against our human design but if it can improve against its previous designs)
	4. NOTES:
		- crucially it's important that we don't accidentally corrupt anything with our existing plugin packages so make sure the plugin package that the agent is allowed to edit is in its own folder(s)
			- would be nice to track versioning of its self authored plugins
			- so between agent edits we should backup each version and have a file tracking version <-> path correspondence
		- recommend you take a look at documentation to understand how these things are implemented:
			- https://code.claude.com/docs/en/sub-agents
			- https://code.claude.com/docs/en/agent-sdk/custom-tools#give-claude-custom-tools


## Exploration Process Advice

The big thing I want you to keep in mind is that these 3 major task categories are fairly "independent" in some weak sense. Not truly independent, but you could imagine doing this in 3 separate sessions. Unfortunately I need to sleep, so I can't manage the 3 sessions and thus need you to handle this in one overnight session. I think maybe the best approach is that after **you reach a stopping point on each task, (1) write a big handoff document detailing everything you explored, did, found for my reviewing tomorrow morning, (2) and then write a short handoff document for the next major task category (3) run `/compact` to save yourself from over-long session context history (4) start next task.**

Remember that this big document of instructions is a file on disk (at `~/sci/repo3/misc/apr30_overnight_instructions.md`) so you can always refer back here.

Some other miscellaneous advice:
- I generally recommend setting workers=6 for runs because that way you can get done with the 17 tasks in 3 batches instead of more
- remember to keep large data outputs on `/data/shared/geophysics_agent_data` because this project's code and some of the data is on the `/home` partition but lab policy is to keep heavy data on the `/data/shared` partition. Obviously (1) stay within the `geophysics_agent_data` subtree on that partition (2) be extremely careful to avoid anything to override existing files and folders
- just like you've been doing here, doing ablation analysis with the tools you've developed to understand why different treatments work/don't work (and analyzing why certain trajectories fail/succeed) is useful

Since I'm going to sleep I need you to make autonomous decisions about what to do. Experiments go fairly fast because we're evaluating so few problems and have the capability to do evaluation in parallel by design. There are roughly 6-7 hours until my next project meeting and would love to present results for all 3 of these. Please use DSv4-flash for all experiments because it's extremely cheap. Please document your work and results as always.
