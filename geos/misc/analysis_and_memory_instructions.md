Ok a couple of items:
0. I really need you to confirm you have been using the v2 specs for these experiments
1. my advisor asked a post doc to help out so I was onboarding them and they blindsided me with a question about why CC itself is not so performant on this task. Because when I presented the task definition: convert this natural language simulation spec into the XML simulation, we all think that intuitively being able to read docs and examples should make this task easy for CC + current models. So the first question is analysis: what is hard about this task? How is the vanilla CC (no plugin) failing? How is our setup failing?
	- We need to do failure analysis to understand what's hard about this task because this is crucial for the discussion section and how we motivate additional features, development, etc.

2. Memory
	1. top level concern is that memory and SR not stacking is bizarre, but I think I'm willing to hazard a guess that our current implementation of memory may be strange as well causing this issue
	2. I think you explained to me that for some reason we're using lexical search. Lexical search in 2026 seems unheard of to me. I thought we have graduated to semantic similarity (embedding based similarity) by now. Feel free to correct if I'm wrong
	3. I understand that embedding stuff is currently blocked on OPENAI_API_KEY not being available. Instead please just use OpenRouter for our embedding API needs. See: https://openrouter.ai/docs/api/reference/embeddings
	4. Ok let's discuss memory implementation again.
		1. did you even implement gmemory based on repo 2 (`/home/matt/sci/geos_agent/modules/memory/gmemory`)?
		2. I finally looked into G-Memory. This looks like it's for multi-agent. We are currently single agent, but I guess maybe some design considerations still apply
		3. Related to our initial human intuition that this task shouldn't be that hard, the post doc was surprised by the choice of G-Mem and that it might be overkill-- thoughts?
	5. Can we fall back on more straight forward approaches (I encourage you to download paper html, convert to markdown programmatically, then read the papers if needed; clone the associated repos for implementation guidance as needed)
		1. Dynamic Cheatsheet: 
			- paper: https://arxiv.org/html/2504.07952v1
			- repo: https://github.com/suzgunmirac/dynamic-cheatsheet
			- note: the simplest form of memory in my opinion (no retrieval, just adding takeaways to a single persistent text artifact-- for our implementation I hope that you are saving copies of the cheatsheet to inspect)
		2. ACE
			- paper: https://arxiv.org/html/2510.04618v3
			- repo: https://github.com/ace-agent/ace
			- note: the direct successor to Dynamic Cheatsheet that is more agent oriented 
		3. ReasoningBank
			- paper: https://arxiv.org/html/2509.25140v1
			- repo: https://github.com/google-research/reasoning-bank
			- note: has retrieval
		 4. MemEvolve
			 - paper: (only available as a pdf) https://arxiv.org/pdf/2512.18746
			 - repo: https://github.com/bingreeky/MemEvolve
			 - note: this is a meta-memory approach that is about changing the design, the key thing to note is that they survey 12 memory methods in the paper that might be worth considering. If you could survey them that would be appreciated.
	6. So to sum up my memory concerns they are (a) it's baffling that it doesn't behave well with self-refinement (b) our current implementation uses some crazy choice (lexical similarity for retrieval) (c) our current memory type of gmemory is bizarre because it feels like overkill and I would prefer to see either simpler memory approaches help us improve together with RAG + SR, OR concrete justification for this complexity that ties into the analysis I requested on existing failure modes
