---
type: Module
title: Brave Search Tool
description: Custom Brave Search API client (web + news) with Pydantic request/response models.
resource: search_tool.py
tags: [search, brave-api, pydantic]
status: stable
---

# Brave Search Tool

`search_tool.py` implements a direct HTTP client against the Brave Search API — a deliberate custom implementation instead of LangChain's built-in `BraveSearch` tool, to get full parameter control and typed validation (see user preference note on search tool choice).

## Models

- **`BaseSearchRequest`** — the 8 fields shared by web and news search: `q`, `country`, `search_lang`, `ui_lang`, `count` (1-20), `offset` (0-9), `spellcheck`, `text_decorations`, `freshness` (`Literal["pd","pw","pm","py"]`). Introduced in the `BaseSearchRequest` refactor to eliminate 8 duplicated field definitions between the web and news models.
- **`SearchRequest`** (extends base) — adds web-specific params: `safesearch`, `result_filter`, `units`, `goggles`, `extra_snippets`, `summary`, `enable_rich_callback`, `include_fetch_metadata`, `operators`.
- **`NewsSearchRequest`** (extends base) — overrides `freshness` default to `"pw"` (past week); otherwise identical to the base.
- **`SearchResult`** / **`SearchResponse`** — normalized output shape (`title`, `url`, `description`, `source`; response wraps a list plus `query`/`count`/`offset`/`took_ms`).

## Functions

- **`search_web(request: SearchRequest) -> SearchResponse`** — GETs `https://api.search.brave.com/res/v1/web/search` with `request.model_dump(exclude_none=True)` as query params and `X-Subscription-Token` from `Settings().brave_search_api_key`. Parses the `web` section of the response (handles both list and `{"results": [...]}` shapes).
- **`search_news(request: NewsSearchRequest) -> SearchResponse`** — GETs `.../news/search`, parses the top-level `results` list, extracting `source.name` when source is a dict.

Both raise `ValueError` if `brave_search_api_key` is unset, and wrap `httpx.HTTPError` into `ValueError` on API failure. Consumed by [`search_graph.py`](/doc/feature/search_graph.md)'s `web_search`/`news_search` LangChain tools.

The `__main__` block runs both functions against live queries as a manual smoke test, logging via [`logging_config`](/doc/feature/logging_config.md) (no `print()`, per the logging cleanup commit).
