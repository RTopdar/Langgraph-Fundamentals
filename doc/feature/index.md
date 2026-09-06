---
type: Bundle Index
title: langgraph-learn architecture
description: OKF bundle indexing this project's modules, services, and scripts.
status: stable
---

# langgraph-learn — Architecture Bundle

OKF (Open Knowledge Format v0.2) bundle. Each file below is one concept document. Traverse via links, not by reading the repo's source tree directly, when answering "how does X work" questions.

## Overview

**Start here:**
- [Architecture Overview](/doc/feature/architecture_overview.md) — high-level system design: chatbot + search graph + Brave Search tool integration

## Concepts

- [Basic Chatbot](/doc/feature/basic_chatbot.md) — `1-basic-chatbot.py`, minimal single-node LangGraph chatbot (learning script, not registered in `langgraph.json`)
- [Search Graph](/doc/feature/search_graph.md) — `search_graph.py`, tool-calling agent looping over Brave web/news search (registered in `langgraph.json`)
- [Brave Search Tool](/doc/feature/search_tool.md) — `search_tool.py`, custom Brave Search API client with Pydantic models (`BaseSearchRequest`/`SearchRequest`/`NewsSearchRequest`)
- [Settings & Model Config](/doc/feature/settings_and_model_config.md) — `settings.py` + `model_config.py`, env-driven config and shared LLM client factory
- [Logging](/doc/feature/logging_config.md) — `logging_config.py`, shared structlog setup used across all modules

## Related

- [doc/index.md](/doc/index.md) — index of indexes for both `doc/` bundles
- [doc/bug/index.md](/doc/bug/index.md) — incident index (bug side of `doc/`)
- [IMPLEMENTATION_PLAN.md](/IMPLEMENTATION_PLAN.md) — narrative architecture + open decisions (kept in sync by the doc-sync agent)
