---
type: Incident
title: Wrong dict path for model metadata in graph result
description: Code read result["response_metadata"] but model metadata is actually nested under result["messages"][-1].response_metadata["model_name"].
status: resolved
resource: 1-basic-chatbot.py
tags: [langgraph, response-metadata, keyerror]
---

# INC-002: Wrong dict path for model metadata in graph result

Affects: [basic_chatbot](/doc/feature/basic_chatbot.md)

## Root cause

Code assumed the graph invocation result carried model metadata directly at `result["response_metadata"]`. In practice, the metadata is nested inside the last message of the result: `result["messages"][-1].response_metadata["model_name"]`.

## Resolution method

Updated the access path to read from `result["messages"][-1].response_metadata["model_name"]` instead of the incorrect top-level key.

## Final status

Resolved.
