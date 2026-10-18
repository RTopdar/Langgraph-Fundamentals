---
type: Module
title: Email Classification Models
description: Enums, definitions, Pydantic result model, graph state, and TypeSafe primitive shapes for the email pipeline.
resource: email_classification/enums.py
tags: [email, enums, pydantic, state, typesafe]
status: wip
---

# Email Classification Models

`email_classification/enums.py` holds the data types shared by the email pipeline.

- **`Intent`** (`str` Enum): `question`, `bug`, `billing`, `feature`, `complex`. `INTENT_DEFINITIONS` gives a one-line description of each, used as Choice criteria.
- **`Urgency`** (`str` Enum): `low`, `medium`, `high`, `critical`. `URGENCY_DEFINITIONS` likewise.
- **`EmailClassification`** (Pydantic `BaseModel`): `intent`, `intent_confidence`, `urgency`, `urgency_confidence`, `topic`, `summary`. `topic` and `summary` are not yet filled.
- **`EmailAgentState`** (`TypedDict`, `total=False`): graph state for [`processor.py`](/doc/feature/email_classification_graph.md). Includes `emails`, `current_index`, `current_email`, `classification`, and `is_done`, plus several fields (`email_content`, `search_results`, `draft_response`, and others) that no node uses yet.
- **`TypeSafeChoice` / `TypeSafeNoul` / `TypeSafeScore`** (TypedDicts): descriptions of the three TypeSafe primitive result shapes (choice, yes/no probability, ordered score). Only `Choice` is used in code, via `langchain_typesafe`. These typed-dicts are not referenced by the classifier.
