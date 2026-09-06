# Langgraph Fundamentals

A beginner-friendly starter kit for learning [LangGraph](https://langchain-ai.github.io/langgraph/) — build stateful, tool-using LLM agents step by step, with a working chatbot, a web-search agent, structured logging, and self-documenting incident/architecture docs baked in.

## What's inside

| File | What it teaches |
|---|---|
| `1-basic-chatbot.py` | Simplest possible LangGraph: one node, one edge, a `StateGraph` that calls an LLM. |
| `search_graph.py` | A multi-node agent graph that routes between chat and web/news search tools. |
| `search_tool.py` | Custom Brave Search tool implementation (web + news) using pydantic request models. |
| `settings.py` | Typed app config loaded from `.env` via `pydantic-settings`. |
| `logging_config.py` | Structured logging setup (`structlog`). |
| `model_config.py` | LLM client factory (OpenRouter). |
| `main.py` | Entry point wiring it together. |

Docs live in `doc/` — architecture notes per module (`doc/feature/`) and a running incident log (`doc/bug/`) — see `AGENTS.md` for how they're organized.

## Prerequisites

- Python 3.13+
- [`uv`](https://docs.astral.sh/uv/) for dependency management

## Setup

```bash
git clone https://github.com/RTopdar/Langgraph-Fundamentals.git
cd Langgraph-Fundamentals
uv sync
cp .env.example .env
```

Edit `.env` and fill in the keys you need:

- `OPENROUTER_API_KEY` — required, powers the LLM calls (get a free-tier key at [openrouter.ai](https://openrouter.ai))
- `BRAVE_SEARCH_API_KEY` — required only for `search_graph.py` / `search_tool.py` (free tier at [brave.com/search/api](https://brave.com/search/api))
- `LANGCHAIN_API_KEY` / `LANGSMITH_API_KEY` — optional, for tracing

## Running the examples

```bash
uv run python 1-basic-chatbot.py
uv run python main.py
```

To explore the graphs visually with LangGraph's dev server:

```bash
uv run langgraph dev
```

This uses `langgraph.json`, which currently exposes the `search_graph` graph.

## Project layout

```
.
├── 1-basic-chatbot.py   # Lesson 1: minimal graph
├── search_graph.py      # Lesson 2: multi-node agent w/ tool routing
├── search_tool.py       # Brave Search tool (web + news)
├── settings.py          # Config via pydantic-settings
├── logging_config.py    # structlog setup
├── model_config.py      # LLM factory
├── main.py              # Entry point
├── doc/                 # Architecture + incident docs (OKF format)
├── IMPLEMENTATION_PLAN.md
└── AGENTS.md            # Rules for AI coding agents working in this repo
```

## Contributing / extending

Adding a new lesson or tool? Check `AGENTS.md` first — this repo keeps `IMPLEMENTATION_PLAN.md` and `doc/feature/` in sync with the code, so new modules should get a matching doc entry.

## License

See [LICENSE](LICENSE).
