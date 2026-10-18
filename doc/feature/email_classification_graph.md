---
type: Module
title: Email Classification Graph
description: LangGraph batch pipeline that loads a CSV of emails and classifies each one's intent and urgency.
resource: email_classification/processor.py
tags: [langgraph, email, classification, typesafe]
status: wip
---

# Email Classification Graph

`email_classification/processor.py` builds and compiles the `email_classifier` graph (`app`). It is not registered in `langgraph.json`; it runs via its `__main__` block.

## Graph

```
START -> init -> reader_init -(Command)-> classify -> reader_advance -(Command)-> classify ... -> end
```

- **`init`** — if `state["emails"]` is empty, loads the CSV with `load_emails_from_csv()`. **The path is hardcoded to an absolute path under `/home/rounak/...`.** See IMPLEMENTATION_PLAN.md Open Decisions.
- **`reader_init`** — [`email_reader`](/doc/feature/email_reader.md) `email_reader_init`: picks the email at `current_index` and routes to `classify`, or to `end` if there are no emails.
- **`classify`** — [`intent_classifier`](/doc/feature/intent_classifier.md), with a LangGraph `RetryPolicy(max_attempts=3, backoff_factor=2)`.
- **`reader_advance`** — [`email_reader`](/doc/feature/email_reader.md) `email_reader_advance`: increments the index and routes back to `classify`, or to `end` when done.
- **`end`** — identity node.

State type is `EmailAgentState` from [`enums.py`](/doc/feature/email_classification_models.md). Checkpointing uses `MemorySaver`.

The `__main__` block invokes the graph on thread `"1"` and logs the final state. Only `classification` is populated per email; the result of each email is not accumulated in state, so the final state holds the last email's classification only (inferred from code).

Logging uses stdlib `logging` (`basicConfig` at import), not [`logging_config`](/doc/feature/logging_config.md).
