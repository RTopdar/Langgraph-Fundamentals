---
type: Module
title: Basic Chatbot
description: Minimal single-node LangGraph chatbot used to learn the StateGraph API.
resource: dummies/1-basic-chatbot.py
tags: [langgraph, chatbot, tutorial]
status: stable
---

# Basic Chatbot

`dummies/1-basic-chatbot.py` is a standalone teaching script demonstrating the smallest possible LangGraph app: one `State` (a message list with `add_messages`), one node (`chatbot`, which just calls the model on the current messages), wired `START → llmchatbot → END`.

Moved from the repo root into `dummies/` in commit `8e48c33`.

It gets its model from [`model_config.get_model()`](/doc/feature/settings_and_model_config.md) and logs via [`logging_config`](/doc/feature/logging_config.md). At the bottom it runs one `graph.invoke()` and one `graph.stream()` call against hardcoded example prompts, purely for demonstration — there's no CLI or reusable entrypoint.

The block that renders `graph.png` via `draw_mermaid_png()` is commented out.

Not registered in `langgraph.json`. See [Architecture Overview](/doc/feature/architecture_overview.md).
