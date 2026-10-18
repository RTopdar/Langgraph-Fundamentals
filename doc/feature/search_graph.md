---
type: Module
title: Search Graph
description: Tool-calling LangGraph agent that can call Brave web/news search and reason over results.
resource: dummies/search_graph.py
tags: [langgraph, agent, search, tools]
status: stable
---

# Search Graph

`dummies/search_graph.py` is the main search-capable agent in this repo. It was moved from the repo root into `dummies/` in commit `8e48c33` and imports `dummies.search_tool`, so run it from the repo root.

**Drift:** `langgraph.json` still maps `search_graph` → `search_graph:graph`, which no longer resolves. Until that is fixed (see IMPLEMENTATION_PLAN.md Open Decisions), `langgraph dev` will not load this graph.

## State

`State` holds `messages` (standard `add_messages` reducer) and `search_results` (last-write-wins list), populated by the `process_tool_result` node.

## Tools

Two LangChain tools wrap the raw functions from [`search_tool.py`](/doc/feature/search_tool.md):

- `web_search(query, count=5, safesearch, freshness, country)` → builds a `SearchRequest`, calls `search_web()`.
- `news_search(query, count=5, freshness="pw", country)` → builds a `NewsSearchRequest`, calls `search_news()`.

Both cap `count` at `min(count, 5)` before calling the underlying API, even though the Pydantic models allow up to 20 (see Open Decisions in [IMPLEMENTATION_PLAN.md](/IMPLEMENTATION_PLAN.md)). Both are decorated `@tool` + `@traceable` for LangSmith visibility, and return JSON strings (results or an `{"error": ...}` payload on failure).

## Graph shape

```
START -> agent -(tools_condition)-> tools -> process_tool_result -> agent -> ... -> END
```

- **`agent`** — injects a system prompt with the current date/year and freshness-code guidance (`pd`/`pw`/`pm`/`py`), binds `[web_search, news_search]` to the model, and invokes it.
- **`tools`** — a prebuilt `ToolNode` executing whichever tool(s) the model called.
- **`process_tool_result`** — walks trailing `ToolMessage`s, parses their JSON content, and collects `results` into `state["search_results"]` (skips empty content, logs and skips entries with an `"error"` key or malformed JSON).

Checkpointing uses `MemorySaver`, with `interrupt_before=["tools"]` for human-in-the-loop approval of tool calls.

LangSmith tracing is enabled here independently of `main.py`, directly from `Settings()` at module import time.

The `__main__` block runs three manual smoke tests (simple query, freshness-filtered query, multi-turn conversation) and, on success, writes `graph.png` via `draw_mermaid_png()` to the current working directory.
