---
type: Module
title: Logging
description: Shared structlog setup used across all runnable modules instead of print().
resource: logging_config.py
tags: [logging, structlog]
status: stable
---

# Logging

`logging_config.py` provides `setup_logging(log_level="INFO")` and `get_logger(name)`, wrapping `structlog` with:

- colorized console rendering (`structlog.dev.ConsoleRenderer(colors=True)`)
- a custom `format_json_fields` processor that pretty-prints dict/list values in log events for readability
- ISO timestamps, stack/exc info rendering, and standard-library logging bridged through `logging.basicConfig`

Most runnable modules ([`dummies/1-basic-chatbot.py`](/doc/feature/basic_chatbot.md), `main.py`, [`dummies/search_graph.py`](/doc/feature/search_graph.md), [`dummies/search_tool.py`](/doc/feature/search_tool.md), [`model_config.py`](/doc/feature/settings_and_model_config.md)) call `setup_logging()` once at import time and get a module logger via `get_logger(__name__)`.

**Exception:** the `email_classification/` modules use stdlib `logging`. [`processor.py`](/doc/feature/email_classification_graph.md) calls `logging.basicConfig` directly and the node tools use `logging.getLogger`. This is an open decision in IMPLEMENTATION_PLAN.md.

`print()` calls in `dummies/search_graph.py` and `dummies/search_tool.py`'s test/`__main__` code were replaced with `logger.info()` for consistent structured logging (see commit `0d623f4`) — the only remaining `print()` calls are in the `graph.png` export error handlers, which run before logging concerns matter.
