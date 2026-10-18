---
type: Module
title: Intent Classifier
description: LangGraph node that classifies an email's intent and urgency with TypeSafe Choice primitives.
resource: email_classification/node_tools/intent_classifier.py
tags: [email, typesafe, classification, retry]
status: wip
---

# Intent Classifier

`email_classification/node_tools/intent_classifier.py` implements the `classify` node used by [`processor.py`](/doc/feature/email_classification_graph.md).

## Behavior

1. Reads `current_email` from state. Returns `{}` if it is missing.
2. Builds a `langchain_typesafe.TypeSafeClassifier(api_key=Settings().typesafe_api_key)`. See [Settings & Model Config](/doc/feature/settings_and_model_config.md).
3. Asks two `Choice` questions over the email body:
   - `intent` — one of `question`, `bug`, `billing`, `feature`, `complex` (definitions in [`enums.py`](/doc/feature/email_classification_models.md)).
   - `urgency` — one of `low`, `medium`, `high`, `critical`.
4. Retries the `invoke` call with tenacity (3 attempts, exponential backoff, 2–10s). The `classify` node also has a LangGraph `RetryPolicy`, so failures can be retried at two levels (inferred from code).
5. Maps the choices to an `EmailClassification` (confidences from TypeSafe). `topic` and `summary` are set to `""`.
6. Returns `{"classification": ...}`. On an unhandled error it logs and re-raises.

## Known issues

- Logs the first 10 characters of the API key on every call (inferred from code, probably unintended).
- `settings = Settings()` runs at import time.
