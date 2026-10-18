---
type: Module
title: Email Reader
description: CSV loader and Command-based routing that steps through emails one at a time.
resource: email_classification/node_tools/email_reader.py
tags: [email, csv, langgraph, command]
status: wip
---

# Email Reader

`email_classification/node_tools/email_reader.py` loads emails and provides the two routing nodes used by [`processor.py`](/doc/feature/email_classification_graph.md).

- **`load_emails_from_csv(path)`** — reads `email_id, sender_email, email_content, source_type, source_queue, source_priority` with `csv.DictReader`, strips values, returns a list of `Email` TypedDicts. Returns `[]` on a missing file or any error (logged).
- **`email_reader_init(state)`** — if there are emails and `current_index` is in range, sets `current_email` and routes to `classify`; otherwise sets `is_done` and routes to `end`.
- **`email_reader_advance(state)`** — increments `current_index`, sets the next `current_email`, and routes to `classify`; at the end of the list sets `is_done` and routes to `end`.

Its module docstring still describes an older column set (`id, subject, body, sender, timestamp`). The code and `dummy_emails.csv` use the columns listed above (inferred from code).
