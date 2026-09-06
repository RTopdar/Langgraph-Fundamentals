# Implementation Plan — langgraph-learn

Narrative architecture and open decisions for this project. Kept in sync with the codebase by the doc-sync flow (AGENTS.md rule #4). Treat drift between this file and the actual code as a bug.

## Status

Prototype / learning repo. Two standalone graphs exist: a minimal single-node chatbot (`1-basic-chatbot.py`, exploratory script) and a more complete tool-using search agent (`search_graph.py`, wired into `langgraph.json` for `langgraph dev`). No test suite yet.

## Components

- **`1-basic-chatbot.py`** — minimal single-node LangGraph chatbot (START → llmchatbot → END) used to learn the basic StateGraph API. Run directly as a script; not registered in `langgraph.json`.
- **`main.py`** — small entrypoint that loads `Settings`, configures logging, and conditionally enables LangSmith tracing via env vars. Doesn't build or run a graph itself.
- **`search_graph.py`** — the main learning artifact: a tool-calling LangGraph agent (agent → tools → process_tool_result → agent loop) that can call Brave web/news search and reason over results. Registered in `langgraph.json` as the `search_graph` graph for `langgraph dev`.
- **`search_tool.py`** — Brave Search API client. Pydantic request/response models (`BaseSearchRequest`, `SearchRequest`, `NewsSearchRequest`, `SearchResult`, `SearchResponse`) plus `search_web()`/`search_news()` functions that call the Brave HTTP API directly (custom implementation, not LangChain's built-in `BraveSearch` tool — see decision below).
- **`settings.py`** — `pydantic_settings.BaseSettings` subclass loading config from `.env` (OpenRouter key/model, LangChain/LangSmith keys, Brave Search key, log level, app name).
- **`model_config.py`** — `get_model()` factory returning a configured `ChatOpenRouter` instance (temperature 0.7, 3 retries) built from `Settings`.
- **`logging_config.py`** — `structlog` setup (`setup_logging()`, `get_logger()`) with colorized console output and pretty-printed JSON fields for structured logs; used by every other module instead of `print()`.
- **`langgraph.json`** — LangGraph CLI/dev config; exposes only `search_graph:graph` (the basic chatbot graph is not registered here).
- **`pyproject.toml`** — uv-managed project, Python >=3.13; key deps: `langgraph`, `langgraph-cli[inmem]`, `langchain-openrouter`, `pydantic-settings`, `structlog`.

## Architecture

- **LLM access is centralized**: every graph gets its model via `model_config.get_model()`, which reads `Settings` (OpenRouter key/model). No module constructs a `ChatOpenRouter` directly.
- **Config is centralized**: `settings.py` is the single source of truth for all env-derived config (LLM, Brave, LangSmith, logging). Both `main.py` and `search_graph.py` instantiate `Settings()` independently to decide whether to enable LangSmith tracing.
- **Logging is centralized**: `logging_config.setup_logging()`/`get_logger()` (structlog) is called at the top of every runnable module; `print()` has been fully replaced by structured logger calls (see commit `0d623f4`).
- **Search is a custom Brave API client, not LangChain's built-in tool**: `search_tool.py` implements `search_web`/`search_news` directly against the Brave HTTP API with Pydantic validation, instead of using LangChain's `BraveSearch` wrapper. This is a deliberate preference (see user memory note `search_tool_choice.md`) for full parameter control and typed request/response models.
- **Shared search parameters are deduplicated via inheritance**: `BaseSearchRequest` holds the 8 fields common to both web and news search; `SearchRequest` (web) and `NewsSearchRequest` (news, `freshness` defaulting to `"pw"`) both inherit from it (commit `03f88f9`), so Pydantic validation (e.g. the `freshness` Literal) lives in one place.
- **`search_graph.py` wraps the raw search functions as LangGraph/LangChain tools** (`web_search`, `news_search`) with `@tool` + `@traceable`, capped at `count=5` regardless of caller-requested count, and adds a `process_tool_result` node that parses `ToolMessage` JSON payloads back into a `search_results` state field for downstream use — this is separate from the raw model tool-calling loop (`agent` → `tools_condition` → `tools` → `process_tool_result` → back to `agent`).
- **`1-basic-chatbot.py` is a standalone teaching script**, not part of the `search_graph` app; it is not registered in `langgraph.json` and has no CLI entrypoint via `main.py`.
- **`langgraph.json` only exposes `search_graph`** for `langgraph dev`/Studio; the basic chatbot remains a plain Python script run directly.

## Open Decisions

- Whether `1-basic-chatbot.py` should eventually be registered in `langgraph.json` alongside `search_graph`, or stays a disposable teaching script (inferred: currently treated as disposable — no graph.png regeneration path, PNG export code is commented out).
- `web_search`/`news_search` in `search_graph.py` silently cap `count` at 5 even though `SearchRequest`/`NewsSearchRequest` allow up to 20 — not documented to the LLM in the tool's stated range (1-20). Likely intentional cost/latency control, but not explicitly recorded as a decision anywhere (inferred from code).
- No test suite exists yet for `search_tool.py`'s Brave API parsing logic or `search_graph.py`'s routing; `__main__` blocks in both files serve as manual smoke tests only.
- `main.py` and `search_graph.py` each duplicate the "load Settings, conditionally enable LangSmith env vars" logic — not yet unified into a shared helper.

## Changelog

- 2026-09-07: Initial fill of IMPLEMENTATION_PLAN.md from empty template — documented all 7 root modules, `langgraph.json`, and architecture connecting chatbot/search graph/tools/settings/logging. Created `doc/feature/architecture_overview.md` plus one concept doc per module and updated `doc/feature/index.md`.
