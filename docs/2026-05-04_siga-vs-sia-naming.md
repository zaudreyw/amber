# Naming: SIGA (with "Grounding") vs SIA (without)

*Generated 2026-05-04. Records the rationale for keeping "Grounding" in the method name. Author: research-copilot, in response to advisor pushback (re-instate "Grounding") and user pushback (don't love it).*

## TL;DR

Use **SIGA** (Simulator-Interface Grounding Adapter). The word "Grounding" is doing real load-bearing work — it names *the mechanism the method actually uses* — and "Adapter" alone is too generic to differentiate the contribution from countless other adapters in ML. Three reasons follow.

## 1. "Grounding" is established ML terminology that names exactly what we do

In modern agent and LLM literature, **grounding** has a precise and widely-recognised meaning: connecting the model's outputs to some external reference frame so that they are not free-floating natural language.

- *Visual grounding*: tying language to image regions (Yu et al., RefCOCO 2016; CLIP-style work).
- *Knowledge grounding*: tying generated answers to a retrieved knowledge source (RAG, Atlas, REALM).
- *Tool grounding*: tying the agent's actions to a documented external API surface (Toolformer, Gorilla, ChemCrow).
- *Code grounding*: tying generation to a target language's parser and standard library (Codex, code-execution-feedback work).

What our method does is straightforwardly an instance of this pattern: the agent's outputs (XML decks) are grounded in (a) the simulator's documented vocabulary and schema (the simulator's *internal API*), (b) the simulator's example library (executable analogues), and (c) the simulator's parser (a hard-correctness signal via xmllint and the bounded repair loop). Reviewers reading "Grounding Adapter" will land on this interpretation immediately. Reviewers reading "Adapter" alone will think parameter-efficient fine-tuning (LoRA-style) and have to read several paragraphs to discover that we mean something else.

## 2. "Adapter" alone collides with a much more famous term

Search Google Scholar for "adapter" + "language model" and you get hundreds of papers, almost all about parameter-efficient fine-tuning (Houlsby et al. 2019, LoRA, AdapterFusion, AdapterHub). Our method does *not* train, fine-tune, or modify model weights at all. The connotation collision actively hurts the paper:

- A reviewer who misreads "Simulator Interface Adapter" as a parameter adapter will then evaluate it against the parameter-efficient adapter literature, find we're missing baselines (LoRA on what? what fraction of params trained?), and lower the score.
- The disambiguation "we adapt the harness, not the model" is a sentence we'd have to write in the abstract, intro, and method section. With "Grounding" in the name, the disambiguation is implicit: nobody talks about "grounding adapters" in the LoRA sense.

Adding "Grounding" buys us free disambiguation that we'd otherwise pay for in word count.

## 3. The advisor's framing aligns with the use-inspired NeurIPS submission type

We're submitting under "Use-inspired: the main contribution is in framing or designing approaches to meet the needs of a specific real-world application. (This often involves, e.g., engaging with domain experts.)" Use-inspired submissions are evaluated heavily on whether the *framing* and *design* are coherent and motivated. The grounding framing is the cleanest motivating story we can tell:

- *Problem framing*: scientific simulators expose their capability through a DSL whose vocabulary is a particular simulator's internal API; the agent must produce exact tokens of that vocabulary, not approximate natural language.
- *Method framing*: SIGA grounds the agent in that vocabulary by exposing it as retrieval, by always-on prompting (the primer), by parser-level verification, and by repair feedback.
- *Contribution framing*: the recipe is GEOS-instantiated but recipe-portable to any simulator that exposes documentation, examples, schema, and a parser — which is essentially all of them.

Each of those three sentences uses the word "ground" or a near-synonym implicitly. Putting it explicitly in the method name keeps the throughline visible.

## What "Grounding" is *not* doing

To be honest about the failure modes of this naming choice:

- It is *not* sensorimotor grounding (Harnad 1990). We are not connecting symbols to perceptual experience. A pedantic reader could complain that the term is being borrowed loosely. We treat that as a minor cost; the broader use of "grounding" in NLP/agent literature has clearly drifted from the philosophical sense.
- It is *not* a single technical mechanism — it is the umbrella term for the four components. Reviewers may ask "but which component does the grounding?" The answer (all four, at different levels) is fine, but we should be ready to make it explicit in the method section.
- It does add a syllable to the method name. The acronym SIGA reads slightly less cleanly than SIA. We treat this as a small cost relative to the disambiguation benefit.

## Decision

Use **SIGA** (Simulator-Interface Grounding Adapter). Hyphenate "Simulator-Interface" to make it clear that "Interface" modifies "Simulator" (the interface *to* the simulator), not "Grounding" (we are not grounding the interface). Pronounce "see-gah" or "sigma minus the m" — short enough to use as an in-text noun.

Method-section opening sentence (proposal):

> We propose a Simulator-Interface Grounding Adapter (SIGA) — a wrapper around a general-purpose coding harness that grounds the agent's generated artefacts in the target simulator's documented vocabulary, executable example library, and parser. SIGA is a recipe with four components — interface retrieval, an always-on interface primer, an output verifier, and bounded repair hints — that together expose the simulator's interface to the agent through the channels coding harnesses already support.
