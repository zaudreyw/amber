This is the geophysics GEOS agent project.
## Introduction

GEOS is an advanced multiphysics simulator developed by folks at LLNL, Stanford, etc.

Partially related to how powerful/flexible it is, GEOS is complicated and not easy to learn or use. The goal for our project is to develop an agent to ease the burden on geoscientists looking to use GEOS by automating usage of this software. One of the challenges that AI agents are best suited to aid in the usage of GEOS is setting up simulations which involves preparing XML files to configure a given simulation.

The initial task for the agent is then:
- given: natural language specification of a simulation to run
- do: create the XML configuration files and run the simulation.

The team working on this project mostly have CS, NLP, and AI backgrounds. We are working with some domain experts in professors from another university in their geoscience department and some of their grad students, and one of the LLNL affiliated developers of GEOS itself. It should be noted that these domain experts are somewhat hard to reach and our interface is limited, so any requests from them generally have to be short requests and we should try to make it as easy for them as possible (reduce the burden on them however we can).

## Further Evaluation Details

We current construct our evaluation set from documentation examples which correspond with a tutorial documentation page (.rst from sphinx/readthedocs) and corresponding ground truth .xml files for the actual simulation.

Metrics:
- The way we evaluate the agent's correctness/accuracy is to compute a kind of XML tree similarity score that recursively checks for node similarity.
- We are interested in the following secondary metrics regarding efficiency:
	- wall clock time (per task, per worker): on average how long did a worker take to finish one task
	- token usage: average input and output tokens per task
	- API costs: (token usage multiplied by pricing)
	- tool call counts

Please note that we provide the entire GEOS source repo to the agent to explore. Crucially this contains the documentation and the XML files mentioned in the documentation. Since our test examples are basically these XML files we have a decontamination guardrails:
- We make a de-contaminated copy of the  GEOS source repo that hides the ground truth XML and RST files corresponding to the task being evaluated
- The CC instance is spun up in a docker container that only can see this decontaminated copy and not the original repo 

### On Controlling Difficulty

Regarding what exactly is included in the task input, we assert that there are certain config values (which correspond to XML elements, tags, and attributes/parameters) that are required and must be provided to the agent to specify what the simulation is even about. The non-required set of config values are treated as "inferable"-- we would expect an agent to be able to fill in this blank reasonably.

There exists a tradeoff where if we assume all values are required, then the agent is less useful to the scientist because the scientist must do more legwork. On the other hand, if we presume more values are inferable then we may unfairly be evaluating agents, assigning overly low scores due to the generated XML having mismatched values because they were not specified by the user.

The problem is that the classification relies on a domain expert to help us navigate, but we don't have domain expert time to hand classify all parameters for all simulations we want to test. Instead we are relying on you the agent to use your knowledge to prepare a classifier program that uses both purely programmatic rules and natural language rules (in a prompt for an LLM query) to perform this classification.

The binary classification gives us 2 possible evaluations-- 'easy' and 'hard'.
- easy presume all values are required and provides all of them in the natural language spec
- hard only includes required values in the spec

One idea we considered previously is trying to implement a gradient of difficulty-- i.e. adding intermediate stages between 'easy' and 'hard'. This initial attempt classified values into different categories:
- software_default: output format, restart frequency, event scheduling, log levels, lookup-table interpolation method
- standard_numerics: newton tolerance, linear solver, preconditioner, max iterations, time-step limits, discretization
- domain_inferrable: water viscosity at reservoir conditions, CO2 molar weight, typical reservoir porosity, etc.
- problem_defining: domain dimensions, well locations, injection rate, etc.

Please see `/home/matt/sci/geos_agent/cc_docs/difficulty_tiers_pitch.md` for more details

On initial discussion with our domain expert, the feedback I received was that our categorization is more categorical than tiered. There's less of a hierarchy. Do you agree? Is there a difficulty curve in how hard it would be to pick reasonable values?

- maybe we can reduce the number of tiers?

I guess it depends on what we would expect the agent to do to pick reasonable values. For some of the parameters it may be as easy as looking at other example XML files, while some particularly domain related parameters might require referencing external material property databases or searching and reading other papers in the domain to see what other researchers have done.

I'm interested in exploring at least a binary version of the difficulty tiers because I think the harder task could demonstrate greater utility for the geoscientists we are trying to help ultimately. Moreover the harder the task, the more opportunity we have to design custom interventions to improve over off-the-shelf solutions.

The current set of instructions we're testing is on the "easy" setting because this requires no domain expertise.
- it was produced from `/home/matt/sci/initial_geos_agent/scripts/mine_examples.py`

The initial difficulty pitch was implemented in: `/home/matt/sci/initial_geos_agent/scripts/mine_examples2.py`

## Multiple Repository History

When we first started this project we initially built an agent from scratch.
- This was a standard coding agent tool with read/write files, bash tools, python execution tools, etc.
- The main adaptation was how we tried to implement domain adaptation by creating a RAG tool specifically for the GEOS documentation
	- This had a special design with 3 different databases it could search
		- documentation: .rst
		- XML files: the documentation examples refer to XML files in small snippets, we created a proper index for the entire XML files
		- schema: the documentation folder has a specific subsection `Datastructure Index` which contains 2 subsections: Input Schema Definitions, and Datastructure Definitions
			- per domain expert advice we treated these reference tables as special entities and allowed the agent to search against this
	- We used chromaDB as our engine for embedding search
	- We also played around with agent-based navigation-- XML snippets in RST files contained path information and the agent could navigate to this file and read it on its own.
- The other piece of domain adaptation was assembling a primer-- a markdown document giving a run down on GEOS to help the agent get started. This was created by using Claude Code incidentally.
- Please see "repo 1" at `/home/matt/sci/initial_geos_agent`

One of our collaborators put together an agent framework for embodied agents that implements many papers' ideas as hot-swappable modules that are plug and play. Per our advisor's suggestion we reimplemented our agent in this framework so we can easily run ablation experiments with different modules.
- Please see "repo 2" at `/home/matt/sci/geos_agent`

We initially intended to compare our custom agent built and rebuilt against an off-the-shelf baseline of Claude Code. We found that on model-normalized settings (using the same model, only changing the harness) that Claude Code outperformed our system (on the current only setting we are considering setting: easy). This was a little frustrating but it makes sense because the Claude Code Harness is an immensely successful commercial product from a top AI research lab while our agent was assembled mostly on vibes and what ideas might be cool. Secondly, embedding based/vector DB RAG approaches are often associated with augmenting LLMs with a huge store of information. While the GEOS documentation is quite rich, it is also well organized, potentially lending well to the Claude Code which is extremely adept at navigating file trees to find it. Our current thought is that Claude Code is extremely well engineered and our task is neither big enough nor hard enough for a specialized design to outperform an extremely tuned general coding agent.

That's fine we decided to make another pivot and then implement our agent ON TOP of Claude Code because science and engineering is all about standing on the shoulders of giants. The new thrust of the paper is then about our adaptation and experiments with the Claude Code harness to see what is effective for our task. This effort has been developed in `repo3` which is now what we are considering our "main" repo where we want all developments to live from here on out. The adaptations on top of Claude Code harness are implemented as a plugin which contains custom skills, tools, so on. Besides the plugin we are considering external interventions to be discussed later.

So negative results can be instructive for the paper to show that XYZ components are not necessary for the task and may degrade performance, but what is important to us is that there is SOME adaptation that can improve performance on our task. Otherwise the method we label "ours" in the main table amounts to just the stock Claude Code harness which is not a research/methodological contribution.

I have some ideas I think may be fruitful which we'll detail later, but I highly encourage you to come up with your own proposals

## Planned Experiments

For our paper we would like the following:

Table 1: our agent vs. baselines
- our harness (CC + adaptations): test with models
- generic coding agent harness (repo 2 harness)
- agent architecture from other scientific automation papers
- harness-less:
	- prompt the model to generate the XML without doing the whole agentic loop of exploring documentation, just provide some in-context examples

We expect at least some of table 1's rows (including ours, and some key baselines) to be evaluated with several models to show that ours is better regardless of model

The main model candidates are:
- absolute SOTA: Opus 4.6
	- this is grossly expensive so we want to limit this and potentially test a subset
- large open model: Minimax 2.7 or DeepSeek v3.2
- small models:
	- Gemma 4 31B
	- Qwen-3.5 9B*
		- *caveat I personally believe that this model scale (<10B parameters) is not feasible for our task so I plan on only testing vanilla CC (Claude Code without our adaptations) to show that this doesn't work

Table 2: Specific Method Ablations
- impact of removing our adaptations
	- without memory
	- with different memory implementations
- impact of removing the GEOS primer 

Table 4: evaluation difficulty
- compare performance of maybe different setups against different evaluation difficulty settings ("easy" vs. "hard")

## What experiments we already have

The first order of business is demonstrating that there exists some adaptation you can make to CC to make it more performant on your task.

So my collaborator Brian has re-implemented our custom adaptations (custom RAG mostly) as a plugin for CC to see if what we already designed based on vibes only for our initial agent helps CC.

So we have a couple of initial results
- from my collaborator:
	- CC + plugin (custom RAG v0) with model:DeepSeek v3.2 (unscored), see outputs at: `data/eval/claude_code_repo3_plugin/repo3_eval_run4`
- my runs: (please read )
	- vanilla CC with model:DeepSeek v3.2
	- vanilla CC with model:DeepSeek v3.2 but the primer is not in the system prompt but a file in the file system the agent can read 
	- vanilla CC with model:Qwen3.5-9B

Some context:
- previously we were using Minimax M2.7 but hit some problems with it so we wanted to use DeepSeek
- we found that DeepSeek runs tended to timeout more often on the 10 minute limit, so we expanded to 20 minutes, but it seems to still be timing out

## Ideas I have

Ok so the first priority is to figure out what adaptation can let us improve over vanilla CC because without this there is 0 method contribution. Having the paper takeaway being that "oh just use CC lmao" is not satisfying. Here are things I think could help.

- the primer itself
	- currently this is implemented as being embedded in the system prompt
	- you may realize that this is similar to CLAUDE.md which is constructed from /init
	- in some ways you could describe this adaptation as "make sure to run /init on the target software repo" which is questionably not an adaptation but something vanilla already supports. They key argument/distinction is that `/init` explores from the current working directory whereas our primer is targeting the software's source/docs directly (if a user is using CC from arbitrary repo, /init doesn't help them).
		- moreover it's more an overview of the documentation/software rather than a map of the repo
	- does the instruction for what to include in the primer/how to structure it matter?
- documentation search aids
	- RAG
		- now we already tried the RAG thing but maybe got too fancy with it
		- one simple approach is to just try a more standard approach to properly rule this out and just blindly chunk the entire documentation into chunks and use a single DB
	- Agentic File Tree Navigation
		- CC already does this, but how can we help this
		- we empirically notice a lot of `ls` and `glob` being used in the inputFiles directory and the documentation folder
		- This isn't a problem itself, but I wonder if having the full file tree in context already can let the agent find exactly what it's looker for without having to reach around and explore
- new knowledge sources
	- so this is more related to the higher difficulty version, but I could imagine connecting CC to a materials property database or give it access to hella geoscience papers/paper search that it could do better on the harder version
	- our domain expert mentioned that he sometimes just relies on searching wikipedia for values like bulk modulus for some material. Then uses textbooks or papers to find more specific details as he needs.
	- since we're currently focusing on efficiency for the easy task maybe this is on the back burner (deprioritized)

Ok so admittedly these ideas are not really innovative, but they are small practical things that may help. I'm somewhat at a loss for how else to improve CC on our task as is, but I do recommend you think about other ideas we could feasibly implement.  If looking at agent outputs is your thing I suggest looking at `/data/shared/geophysics_agent_data/data/eval/claude_code_repo3_plugin/repo3_eval_run2/AdvancedExampleCasedContactThermoElasticWellbore` or other examples to see how our initial plugin was used and `1. /home/matt/sci/geos_agent/runs/t1_cc_deepseek_clean2/AdvancedExampleCasedContactThermoElasticWellbore/cc_conversation.jsonl` for how a vanilla CC harness approaches it instead.

### Memory Ideas

I truly think the big improvement vector lies in having a memory system-- reflecting on previous trajectories and writing down takeaways to improve performance on future runs.

Here are the considerations:
- Built in Memory?
	- Claude Code ships with a memory feature
	- I'm not sure our current evaluation set up even triggers this with the independent containerization
		- my impression is that CC stores memory on the file system on a per project basis (per directory CC is initialized from)
	- moreover, I'm not confident that the memory tool is even being leveraged at all in our current CC experiments-- maybe you could please search through the logs I provided you to see if this is being written to (if not read, due to the containerization stuff I mentioned)
- How to design memory?
	- can start with the minimal "cheatsheet" approach where memory is implemented as a singular text blob
	- can reference memory modules from the embodied agent framework (see memory modules in repo2; the ones we highlighted as possible candidates are):
		- Mem0, Cheatsheet, Buffer of Thoughts, GMemory
- Continually learn memory vs. pre-learn and freeze
	- This is an engineering question but it has some research consequences
	- The consideration is as follows:
		- if you want continual learning, parallelization becomes way harder
			- continual learning implies that before tackling task n+1 you need to update the memory after completing task n. This does not allow you to run task n and n+1 at the same time.
			- There are some workarounds like batching: you only update the memory after several tasks, therefore each batch can be run simultaneously
				- This adds some challenge as to how to reflect on multiple trajectories simultaneously
					- one solution (unclear how good this is) is to reflect on each trajectory independently and then aggregate these reflections into a single memory update?
		- The alternative to continual learning is to hold out a fixed set of tasks as "train set" and then get trajectories/reflections/memory updates for those, then freeze the memory and make it read only for all the remaining test tasks which can be parallelized again
			- my initial preference is to do this frozen thing because parallelization is very important for getting lots of runs in given our time constraints
- Assume access to labels or no
	- often times self reflection/self improvement strategies for AI agents benefit if they have some grounding for them  to compare their trajectory against. This may come as a correct final answer, or test case results, etc.
	- In our case we do have the ground truth XMLs but allows the agent to see these at reflection time impacts how the agent's memory learning can be said to act in deployment-- does it need ground truth to update reliably? 
	- My initial bias is to use the label just because we want to demonstrate memory is effective and it's possible for domain experts to provide similar feedback at deployment (this makes it subtly less useful for users that don't know GEOS well)
- Tool based or External
	- so although CC is an interactive tool we are essentially treating it as single text input.
	- As such we can implement memory on the prompt level (i.e. control what context is sent to CC from the "user")-- the memory is external to claude code and operates outside of it
	- The alternative is to implement the memory as a tool that the CC agent can use inside CC like our previous plugin that provides documentation search, but this time provides search memory or read memory or something to that effect.
	- I genuinely don't know what's easier for us right now-- I would prioritize the one you think would be most effective and then fastest to implement/test afterwards

## Practical Advice

We are on a pretty tight time constraint. I need to report to my advisor in ~8 hours from now so I want some good experiments done in the next 8 hours.

Given that we have 46 total examples and we've already partitioned our 36 as the main eval set and 10 for things like few-shot examples, etc. and that we're having to use a timeout set to 20 minutes per task, I would recommend either figuring out a way to speed this up across the board (10 minutes used to be fine-- see `t1_cc_deepseek_clean2` which was vanilla CC harness on repo2-- recommend looking at how repo2 did the cc runs). 

I think one thing we did observe was that having the primer in the prompt actually drastically reduced timeout incidence? That could be the difference since the repo2 version also had it as a prompt and not a file to read. If that run with the primer-in-prompt really solves the timeout stuff can you reduce the timeout limit again?

Anyways I want you to pick a smaller subset to run against so you can explore more hypotheses/experiments in the next 8 hours.

I also want you to use concurrency as much as you can to speed stuff up.

I want you to focus on the cheaper models:
- minimax 2.7: be careful with this one, it's the most expensive we're considering for now
- deepseek 3.2: our main workhorse
- gemma 4 31b: just a nice to have if it can do anything at all, I'm pretty sure the 9b run came back having completely failed so I'm not actually sure if smaller models work on this task

PLEASE BE CAREFUL ABOUT CONTAMINATION-- don't let the agent see files that are essentially ground truth.
- our current measures are ok I think, please don't compromise them on accident

## What I want you to do

Firstly you need to prepare your information. I'm recently adopting some hooks/plugins provided by a collaborator that apparently helps you run more autonomously while I sleep. I think it also provides structure about how you should maintain docs, tasks, etc. So your first order of business is to organize your information/TODOs/docs/etc to fit this new system.

Next I want you to score the run my collaborator did and then compare against my existing runs.

Next I want you to make a plan about what you can achieve in the next 7-8 hours and then autonomously execute on this.

My personal preference is that you 
- do some small experiments with the primer stuff
- do some small experiments with file tree stuff
- do memory experiments!!
- ideally we can keep the current set of evaluation input files. But if none of your experiments are producing improvements (accuracy OR efficiency improvements are both acceptable), then maybe you decide that improvement is only possible on the harder version of the task.
	- In that case then you can go and make mine_examples_v3.py and then run that with a pretty good model like gemini 3 flash and try our adaptations on the new easy/hard task versions.

However I think you understand the overall objective of this research project which is to ultimately help the geoscientists and develop a tool that is maximally helpful to them. What that means for right now is making our agent maximally accurate and efficient (speed and/or cost). I think you know better than me for AI agent design so in that case I'll leave you to optimize however you want.

As always please document your decisions, your experiments (what command was run, path to outputs, key results/analysis), and be good about making git commits to have nice version control.

Ultimately we want to have results finalized in the next week, but I would like some initial key results in 7 hours or so to show my advisor.





