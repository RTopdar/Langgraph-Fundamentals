---
type: Architecture
title: langgraph-learn architecture overview
description: How the basic chatbot, search graph, Brave Search tool, settings, and logging fit together.
resource: langgraph.json
tags: [langgraph, architecture, overview]
status: stable
---

# Architecture Overview

This repo is a LangGraph learning project built around OpenRouter-hosted models. Root-level code is shared infrastructure; the graph examples live in `dummies/` (teaching scripts) and `email_classification/` (active pipeline).

## Graphs

- **[Basic Chatbot](/doc/feature/basic_chatbot.md)** (`dummies/1-basic-chatbot.py`) — single-node chatbot, run as a standalone script. Not registered in `langgraph.json`.
- **[Search Graph](/doc/feature/search_graph.md)** (`dummies/search_graph.py`) — tool-calling agent that can call Brave web/news search and loop until it has an answer. Still referenced by `langgraph.json` as `search_graph:graph`, which is broken after the move (see IMPLEMENTATION_PLAN.md Open Decisions).
- **[Persistence Joke](/doc/feature/persistence_joke.md)** (`dummies/persistence-joke.py`) — two-node joke/explanation graph demonstrating checkpoints and state history.
- **[Email Classification Graph](/doc/feature/email_classification_graph.md)** (`email_classification/processor.py`) — batch pipeline that reads a CSV of emails and classifies each one. Not registered in `langgraph.json`.

## Shared infrastructure

The graphs (and `main.py`) depend on these cross-cutting modules:

- **[Settings & Model Config](/doc/feature/settings_and_model_config.md)** (`settings.py`, `model_config.py`) — env-driven config (resolved from the project root) and a single `get_model()` factory for the LLM client.
- **[Logging](/doc/feature/logging_config.md)** (`logging_config.py`) — structlog setup used by the `dummies/` scripts and `main.py`. The email classification module uses stdlib logging instead.
- **[Brave Search Tool](/doc/feature/search_tool.md)** (`dummies/search_tool.py`) — custom Brave Search API client (web + news), consumed by `dummies/search_graph.py`'s LangChain tools.
- **[Email Reader](/doc/feature/email_reader.md)**, **[Intent Classifier](/doc/feature/intent_classifier.md)**, **[Email Classification Models](/doc/feature/email_classification_models.md)** — the building blocks of the email pipeline. The classifier uses TypeSafe (`langchain-typesafe`).

## How a request flows (search_graph)

1. `dummies/search_graph.py` builds `Settings()`, optionally turns on LangSmith tracing, and gets a model from `model_config.get_model()`.
2. The `agent` node injects a system prompt (with today's date) and calls the model with `web_search`/`news_search` bound as tools.
3. `tools_condition` routes to the `tools` node (a `ToolNode` wrapping both tools) if the model requested a tool call, else straight to `END`.
4. The `tools` node calls into `search_tool.py`'s `search_web`/`search_news`, which hit the Brave Search HTTP API using `settings.brave_search_api_key`.
5. `process_tool_result` parses the JSON `ToolMessage` payloads back into the graph's `search_results` state field.
6. Control returns to `agent`, which either answers or issues another tool call.

## Related

- [Implementation Plan](/IMPLEMENTATION_PLAN.md) — narrative architecture + open decisions
- [doc/feature/index.md](/doc/feature/index.md) — bundle index
