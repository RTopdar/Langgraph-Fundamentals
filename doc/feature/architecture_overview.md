---
type: Architecture
title: langgraph-learn architecture overview
description: How the basic chatbot, search graph, Brave Search tool, settings, and logging fit together.
resource: langgraph.json
tags: [langgraph, architecture, overview]
status: stable
---

# Architecture Overview

This repo is a LangGraph learning project built around OpenRouter-hosted models. It contains two independent graphs and a set of shared infrastructure modules.

## Graphs

- **[Basic Chatbot](/doc/feature/basic_chatbot.md)** (`1-basic-chatbot.py`) — single-node echo-to-LLM graph, run as a standalone script. Not registered in `langgraph.json`.
- **[Search Graph](/doc/feature/search_graph.md)** (`search_graph.py`) — tool-calling agent that can call Brave web/news search and loop until it has an answer. Registered in `langgraph.json` as `search_graph` for `langgraph dev`/Studio.

## Shared infrastructure

Both graphs (and `main.py`) depend on the same three cross-cutting modules:

- **[Settings & Model Config](/doc/feature/settings_and_model_config.md)** (`settings.py`, `model_config.py`) — env-driven config and a single `get_model()` factory for the LLM client.
- **[Logging](/doc/feature/logging_config.md)** (`logging_config.py`) — structlog setup used everywhere instead of `print()`.
- **[Brave Search Tool](/doc/feature/search_tool.md)** (`search_tool.py`) — custom Brave Search API client (web + news), consumed by `search_graph.py`'s LangChain tools.

## How a request flows (search_graph)

1. `search_graph.py` builds `Settings()`, optionally turns on LangSmith tracing, and gets a model from `model_config.get_model()`.
2. The `agent` node injects a system prompt (with today's date) and calls the model with `web_search`/`news_search` bound as tools.
3. `tools_condition` routes to the `tools` node (a `ToolNode` wrapping both tools) if the model requested a tool call, else straight to `END`.
4. The `tools` node calls into `search_tool.py`'s `search_web`/`search_news`, which hit the Brave Search HTTP API using `settings.brave_search_api_key`.
5. `process_tool_result` parses the JSON `ToolMessage` payloads back into the graph's `search_results` state field.
6. Control returns to `agent`, which either answers or issues another tool call.

## Related

- [Implementation Plan](/IMPLEMENTATION_PLAN.md) — narrative architecture + open decisions
- [doc/feature/index.md](/doc/feature/index.md) — bundle index
