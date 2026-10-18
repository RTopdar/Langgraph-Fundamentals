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
- [Architecture Overview](/doc/feature/architecture_overview.md) — high-level system design: root infrastructure, `dummies/` teaching graphs, and the email classification pipeline

## Concepts

### Root infrastructure
- [Settings & Model Config](/doc/feature/settings_and_model_config.md) — `settings.py` + `model_config.py`, env-driven config (incl. TypeSafe key) and shared LLM client factory
- [Logging](/doc/feature/logging_config.md) — `logging_config.py`, shared structlog setup (email pipeline uses stdlib logging instead)

### `dummies/` (teaching scripts, not registered in `langgraph.json`)
- [Basic Chatbot](/doc/feature/basic_chatbot.md) — `dummies/1-basic-chatbot.py`, minimal single-node LangGraph chatbot
- [Search Graph](/doc/feature/search_graph.md) — `dummies/search_graph.py`, tool-calling agent over Brave web/news search (`langgraph.json` path is broken)
- [Brave Search Tool](/doc/feature/search_tool.md) — `dummies/search_tool.py`, custom Brave Search API client with Pydantic models
- [Persistence Joke](/doc/feature/persistence_joke.md) — `dummies/persistence-joke.py`, two-node graph with checkpoint history

### `email_classification/` (active pipeline)
- [Email Classification Graph](/doc/feature/email_classification_graph.md) — `processor.py`, batch graph that loops over emails
- [Email Reader](/doc/feature/email_reader.md) — `node_tools/email_reader.py`, CSV loader and Command-based routing
- [Intent Classifier](/doc/feature/intent_classifier.md) — `node_tools/intent_classifier.py`, TypeSafe intent/urgency classification with retries
- [Email Classification Models](/doc/feature/email_classification_models.md) — `enums.py`, enums, result model, graph state

## Related

- [doc/index.md](/doc/index.md) — index of indexes for both `doc/` bundles
- [doc/bug/index.md](/doc/bug/index.md) — incident index (bug side of `doc/`)
- [IMPLEMENTATION_PLAN.md](/IMPLEMENTATION_PLAN.md) — narrative architecture + open decisions (kept in sync by the doc-sync agent)
