---
type: Incident
title: structlog event kwarg collision crashes chatbot streaming
description: logger.info("streaming event", event=event) collided with structlog's reserved event param, raising TypeError during streaming.
status: resolved
resource: 1-basic-chatbot.py
tags: [structlog, logging, streaming, typeerror]
---

# INC-001: structlog `event` kwarg collision crashes chatbot streaming

Affects: [basic_chatbot](/doc/feature/basic_chatbot.md)

## Root cause

`logger.info("streaming event", event=event)` passed a keyword argument named `event`, which collides with structlog's own reserved `event` parameter (the log message itself is internally bound to `event`). This raised a `TypeError` any time a streaming log line was emitted.

## Resolution method

Renamed the colliding keyword argument from `event` to `stream_event` so it no longer shadows structlog's internal parameter.

## Final status

Resolved.
