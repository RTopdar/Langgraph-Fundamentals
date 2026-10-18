---
type: Module
title: Settings & Model Config
description: Env-driven configuration and the shared LLM client factory.
resource: settings.py
tags: [config, settings, openrouter, model, typesafe]
status: stable
---

# Settings & Model Config

## `settings.py`

`Settings` (a `pydantic_settings.BaseSettings`) is the single source of truth for env-derived config. It loads `PROJECT_ROOT / ".env"`, where `PROJECT_ROOT` is the directory containing `settings.py`, so the `.env` lookup does not depend on the working directory (commit `a5811b1`). See `.env.example`.

- LLM: `openrouter_api_key` (required), `openrouter_model` (default `"openrouter/free"`)
- LangChain: `langchain_api_key`, `langchain_tracing_v2`
- Brave Search: `brave_search_api_key`
- LangSmith: `langsmith_api_key`, `langsmith_project` (default `"langgraph-learn"`)
- TypeSafe: `typesafe_api_key` (used by [`intent_classifier`](/doc/feature/intent_classifier.md))
- App: `log_level` (default `"INFO"`), `app_name` (default `"langgraph-learn"`)

Modules (`main.py`, `dummies/search_graph.py`, `dummies/search_tool.py`, `model_config.py`, `email_classification/node_tools/intent_classifier.py`, `email_classification/processor.py`) instantiate `Settings()` directly rather than sharing a singleton.

## `model_config.py`

`get_model() -> ChatOpenRouter` is the one factory for LLM clients in this repo: reads `Settings()` and returns a `ChatOpenRouter` configured with `temperature=0.7` and `max_retries=3`. Used by [`dummies/1-basic-chatbot.py`](/doc/feature/basic_chatbot.md), [`dummies/search_graph.py`](/doc/feature/search_graph.md), and [`dummies/persistence-joke.py`](/doc/feature/persistence_joke.md). No module constructs `ChatOpenRouter` directly. The email classifier does not use the LLM; it uses TypeSafe.

Its `__main__` block runs a one-off English→French translation as a manual smoke test.
