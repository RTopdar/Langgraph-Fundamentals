---
type: Module
title: Settings & Model Config
description: Env-driven configuration and the shared LLM client factory.
resource: settings.py
tags: [config, settings, openrouter, model]
status: stable
---

# Settings & Model Config

## `settings.py`

`Settings` (a `pydantic_settings.BaseSettings`) is the single source of truth for env-derived config, loaded from `.env` (see `.env.example`):

- LLM: `openrouter_api_key` (required), `openrouter_model` (default `"openrouter/free"`)
- LangChain: `langchain_api_key`, `langchain_tracing_v2`
- Brave Search: `brave_search_api_key`
- LangSmith: `langsmith_api_key`, `langsmith_project` (default `"langgraph-learn"`)
- App: `log_level` (default `"INFO"`), `app_name` (default `"langgraph-learn"`)

Every module that needs config (`main.py`, `search_graph.py`, `search_tool.py`, `model_config.py`) instantiates `Settings()` directly rather than sharing a singleton.

## `model_config.py`

`get_model() -> ChatOpenRouter` is the one factory for LLM clients in this repo: reads `Settings()` and returns a `ChatOpenRouter` configured with `temperature=0.7` and `max_retries=3`. Used by both [`1-basic-chatbot.py`](/doc/feature/basic_chatbot.md) and [`search_graph.py`](/doc/feature/search_graph.md) — no module constructs `ChatOpenRouter` directly.

Its `__main__` block runs a one-off English→French translation as a manual smoke test.
