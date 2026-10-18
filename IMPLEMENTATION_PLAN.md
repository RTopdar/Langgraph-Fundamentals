# Implementation Plan — langgraph-learn

Narrative architecture and open decisions for this project. Kept in sync with the codebase by the doc-sync flow (AGENTS.md rule #4). Treat drift between this file and the actual code as a bug.

## Status

Prototype / learning repo. The original root-level graphs (`1-basic-chatbot.py`, `search_graph.py`, `search_tool.py`) were moved into `dummies/` (commit `8e48c33`). The active work has shifted to `email_classification/`, a LangGraph batch pipeline that reads a CSV of emails and classifies intent/urgency via TypeSafe. `langgraph.json` still points at `search_graph:graph`, which no longer exists at the root (see Open Decisions). No test suite yet.

## Components

### Root

- **`main.py`** — small entrypoint that loads `Settings`, configures logging, and conditionally enables LangSmith tracing via env vars. Doesn't build or run a graph itself.
- **`settings.py`** — `pydantic_settings.BaseSettings` subclass loading config from `PROJECT_ROOT/.env` (OpenRouter key/model, LangChain/LangSmith keys, Brave Search key, TypeSafe key, log level, app name). `PROJECT_ROOT` is exported from this module.
- **`model_config.py`** — `get_model()` factory returning a configured `ChatOpenRouter` instance (temperature 0.7, 3 retries) built from `Settings`.
- **`logging_config.py`** — `structlog` setup (`setup_logging()`, `get_logger()`) with colorized console output and pretty-printed JSON fields; used by most modules instead of `print()`.
- **`langgraph.json`** — LangGraph CLI/dev config; declares `search_graph` → `search_graph:graph`. **Broken**: `search_graph.py` has moved to `dummies/` (see Open Decisions).
- **`pyproject.toml`** — uv-managed project, Python >=3.13; key deps: `langgraph`, `langgraph-cli[inmem]`, `langchain-openrouter`, `langchain-typesafe`, `pydantic-settings`, `structlog`, `tenacity`.

### `email_classification/` (active)

- **`processor.py`** — LangGraph batch graph (`init` → `reader_init` → `classify` → `reader_advance` loop → `end`). Compiled as `app` with `MemorySaver`. Not registered in `langgraph.json`. Runnable via `__main__`.
- **`enums.py`** — `Intent`, `Urgency` enums with definition dicts, `EmailClassification` (Pydantic), `EmailAgentState` (TypedDict), and TypeSafe primitive typed-dicts (`TypeSafeChoice`, `TypeSafeNoul`, `TypeSafeScore`).
- **`node_tools/email_reader.py`** — CSV loader (`load_emails_from_csv`) and the `email_reader_init` / `email_reader_advance` routing functions that return `Command`s to iterate emails.
- **`node_tools/intent_classifier.py`** — `intent_classifier` node: calls `langchain_typesafe.TypeSafeClassifier` with two `Choice` questions (intent, urgency), wrapped in a tenacity retry, and maps results to `EmailClassification`. `topic` and `summary` are currently left empty.
- **`dummy_emails.csv`** — 300-row sample input (`email_id, sender_email, email_content, source_type, source_queue, source_priority`).

### `dummies/` (legacy / teaching scripts, not registered)

- **`dummies/1-basic-chatbot.py`** — minimal single-node LangGraph chatbot (START → llmchatbot → END). Run directly as a script.
- **`dummies/search_graph.py`** — tool-calling LangGraph agent (agent → tools → process_tool_result → agent loop) over Brave web/news search. Imports `dummies.search_tool`, so run from the repo root.
- **`dummies/search_tool.py`** — Brave Search API client. Pydantic request/response models (`BaseSearchRequest`, `SearchRequest`, `NewsSearchRequest`, `SearchResult`, `SearchResponse`) plus `search_web()`/`search_news()` calling the Brave HTTP API directly (custom implementation, not LangChain's built-in `BraveSearch` — see decision below).
- **`dummies/persistence-joke.py`** — two-node joke graph (Generate Joke → Generate Explanation) with `InMemorySaver` checkpointing; prints the checkpoint history for thread `"1"`. Teaches persistence/state history.

### Agents and skills

- **`.claude/agents/incident-handler.md`** — bug/incident subagent (owns `doc/bug/`).
- **`.claude/agents/doc-sync.md`** — this doc-sync subagent (owns `IMPLEMENTATION_PLAN.md`, `AGENTS.md`, `doc/feature/`).
- **`.claude/skills/*`** — symlinks into `.agents/skills/*` (added in `1f3102f`, tracked via `skills-lock.json`). **Currently dangling**: `.agents/skills/` is empty in this checkout.

## Architecture

- **LLM access is centralized**: every graph gets its model via `model_config.get_model()`, which reads `Settings` (OpenRouter key/model). No module constructs a `ChatOpenRouter` directly.
- **Config is centralized**: `settings.py` is the single source of truth for env-derived config (LLM, Brave, LangSmith, TypeSafe, logging). It resolves `.env` from `PROJECT_ROOT` (the directory containing `settings.py`), so config loads regardless of the working directory (inferred from code, commit `a5811b1`). Modules instantiate `Settings()` independently.
- **Classification uses TypeSafe, not an LLM prompt chain (inferred from code)**: `email_classification` calls `langchain_typesafe.TypeSafeClassifier` with `Choice` primitives (see `enums.py` for the matching primitive shapes). Retries are handled by `tenacity` (3 attempts, exponential backoff) at the call site, and additionally by a LangGraph `RetryPolicy` on the `classify` node.
- **Batch iteration uses `Command` routing**: `email_reader.py` decides `classify` vs `end` via `Command(goto=...)`; `processor.py` wires the loop with edges `classify → reader_advance` and dynamic goto back to `classify`.
- **Logging is mostly centralized**: `logging_config.setup_logging()`/`get_logger()` (structlog) is used by the `dummies/` scripts, `main.py`, and `model_config.py`. The newer `email_classification` modules use stdlib `logging` (`processor.py` calls `logging.basicConfig` directly), so the "every module uses structlog" rule no longer holds (see Open Decisions).
- **Search is a custom Brave API client, not LangChain's built-in tool**: `dummies/search_tool.py` implements `search_web`/`search_news` directly against the Brave HTTP API with Pydantic validation. Deliberate preference (see user memory note `search_tool_choice.md`) for full parameter control and typed request/response models.
- **Shared search parameters are deduplicated via inheritance**: `BaseSearchRequest` holds the 8 fields common to both web and news search; `SearchRequest` and `NewsSearchRequest` inherit from it (commit `03f88f9`).
- **`dummies/search_graph.py` wraps the raw search functions as LangChain tools** (`web_search`, `news_search`) with `@tool` + `@traceable`, capped at `count=5`, and a `process_tool_result` node that parses `ToolMessage` JSON back into `search_results`.
- **Checkpointing**: `dummies/search_graph.py` and `dummies/persistence-joke.py` use `MemorySaver`/`InMemorySaver`; `email_classification/processor.py` uses `MemorySaver`. No persistent checkpointer is configured.
- **Email data source**: the CSV path is hardcoded to an absolute path in `processor.py` (`init_node`), not derived from `PROJECT_ROOT`. Note this when moving the project.

## Open Decisions

- **`langgraph.json` points at a missing module** — `search_graph:graph` no longer resolves at the root after the move to `dummies/`. Either move the graph back, update the path to `dummies.search_graph:graph`, or register `email_classification.processor:app`. Decision needed from user; doc-sync does not change code.
- Whether `email_classification` should be registered in `langgraph.json` (and whether `search_graph` should be restored there) — not recorded yet (inferred: currently only exercised via `__main__`).
- `processor.py` hardcodes the absolute CSV path `/home/rounak/Desktop/...`; should be relative to `PROJECT_ROOT` or a setting (inferred from code).
- `intent_classifier.py` logs the first 10 characters of the TypeSafe API key on every call. Likely unintended; consider removing (inferred from code).
- `processor.py` uses stdlib `logging.basicConfig` while the rest of the repo uses `logging_config` (structlog). Decide which logging stack the new module should use (inferred from code).
- `email_reader.py`'s docstring says the CSV has `id, subject, body, sender, timestamp` columns, but the loader reads `email_id, sender_email, email_content, source_type, source_queue, source_priority`. Docstring is stale (inferred from code).
- `EmailClassification.topic` and `summary` are always empty strings — fields exist but no node fills them yet (inferred from code).
- `web_search`/`news_search` in `dummies/search_graph.py` cap `count` at 5 even though the models allow up to 20. Likely intentional cost/latency control, not recorded as a decision (inferred from code).
- `1-basic-chatbot.py` (now `dummies/`) — kept as a disposable teaching script; not decided whether it stays in `dummies/` permanently.
- No test suite exists yet for `search_tool.py`'s Brave parsing, `search_graph.py` routing, or the email classification pipeline.
- `main.py` and `dummies/search_graph.py` each duplicate the "load Settings, conditionally enable LangSmith env vars" logic — not unified.
- `.claude/skills` symlinks are dangling because `.agents/skills/` is empty in the checkout. Either restore the skill files or remove the symlinks and `skills-lock.json` entries (user decision).

## Changelog

- 2026-09-07: Initial fill of IMPLEMENTATION_PLAN.md from empty template — documented all 7 root modules, `langgraph.json`, and architecture connecting chatbot/search graph/tools/settings/logging. Created `doc/feature/architecture_overview.md` plus one concept doc per module and updated `doc/feature/index.md`.
- 2026-10-18: Synced to `b68f4e0..HEAD`. `a5811b1`: added TypeSafe key to `Settings`, `PROJECT_ROOT`-based `.env` loading, `langchain-typesafe` and `tenacity` deps. `8e48c33`: moved `1-basic-chatbot.py`, `search_graph.py`, `search_tool.py` to `dummies/`; added `dummies/persistence-joke.py` and the `email_classification/` pipeline. `1f3102f`: added `.claude/skills` symlinks and `skills-lock.json` (dangling). Flagged `langgraph.json` breakage and open decisions above.
