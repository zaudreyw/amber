Ok for model preferences here's how I want you to decide which model to use:

SOTA
- models:
	- Gemini 3.1 Pro Preview (`google/gemini-3.1-pro-preview`): least expensive and seemingly most performant; prefer this one among this category
	- GPT-5.4 (`openai/gpt-5.4`)
	- Claude Opus 4.6 (`anthropic/claude-opus-4.6`)
- when to use:
	- only when I specifically ask for it. These models are very expensive and potentially slow as well

Middle ground:
- models:
	- Gemini 3 Flash (`google/gemini-3-flash-preview`)
- when to use:
	- when "smart and cheap" does not suffice

Main:
- models
	- DeepSeek V3.2 (`deepseek/deepseek-v3.2`): cheaper but weaker
	- Minimax 2.7 (`minimax/minimax-m2.7`)
- when to use:
	- almost always-- should treat these as the main models to consider

Workhorse:
- models: 
	- gpt-oss-120b (`openai/gpt-oss-120b`)
		- must set reasoning effort set to high to get best accuracy
		- see OpenRouter reasoning effort/reasoning tokens best practices documentation page
- when to use:
	- for easy, bulk tasks
	- it's the weakest model on this list by far but it's also the cheapest

