---
type: Module
title: Persistence Joke
description: Two-node joke/explanation graph with InMemorySaver checkpointing and a state-history printer.
resource: dummies/persistence-joke.py
tags: [langgraph, persistence, checkpoints, tutorial]
status: stable
---

# Persistence Joke

`dummies/persistence-joke.py` is a teaching script for LangGraph persistence. It is not registered in `langgraph.json`.

## Graph

```
START -> Generate Joke -> Generate Explanation -> END
```

- **`Generate Joke`** — asks the model (from [`model_config.get_model()`](/doc/feature/settings_and_model_config.md)) for a joke on `state["topic"]`.
- **`Generate Explanation`** — asks the model to explain the joke in one line.

State is a `JokeState` TypedDict (`topic`, `joke`, `explanation`).

## Persistence

Compiled with `InMemorySaver`. The script invokes thread `"1"` on topic `"pizza"`, then `print_state_history()` lists every checkpoint (step, node, checkpoint id, next nodes, state values) via `get_state_history()`. Checkpoints are lost when the process exits.

Logs via [`logging_config`](/doc/feature/logging_config.md).
