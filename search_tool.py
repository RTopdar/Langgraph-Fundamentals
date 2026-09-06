"""
Brave Search Web API Tool for LangGraph

Implements a comprehensive search tool leveraging the Brave Search API with full parameter support.
Includes Pydantic models for type validation and comprehensive docstrings for Claude understanding.
"""

import httpx
from typing import Optional, Literal
from pydantic import BaseModel, Field
from settings import Settings
from logging_config import get_logger

logger = get_logger(__name__)


class BaseSearchRequest(BaseModel):
    """Base search request with common parameters for both web and news search"""

    q: str = Field(
        ...,
        description="Search query term. Cannot be empty. Max 400 characters and 50 words."
    )

    country: Optional[str] = Field(
        default="US",
        description="Geographic region using 2-letter country codes (e.g., US, GB, AU, CA, etc.). Defaults to US."
    )

    search_lang: Optional[str] = Field(
        default="en",
        description="Language code for results (2+ characters, e.g., 'en', 'es', 'fr', 'de'). Defaults to English."
    )

    ui_lang: Optional[str] = Field(
        default="en-US",
        description="UI language in format language-country (e.g., 'en-US', 'es-ES', 'fr-CA'). Defaults to English-US."
    )

    count: Optional[int] = Field(
        default=20,
        ge=1,
        le=20,
        description="Number of results to return (1-20). Defaults to 20."
    )

    offset: Optional[int] = Field(
        default=0,
        ge=0,
        le=9,
        description="Zero-based pagination offset (0-9 pages). Defaults to 0."
    )

    spellcheck: Optional[bool] = Field(
        default=True,
        description="Enable automatic query spelling correction. Defaults to True."
    )

    text_decorations: Optional[bool] = Field(
        default=True,
        description="Include highlighting markers in display strings. Defaults to True."
    )

    freshness: Optional[Literal["pd", "pw", "pm", "py"]] = Field(
        default=None,
        description="Filter by age. MUST be one of: 'pd' (past day), 'pw' (past week), 'pm' (past month), 'py' (past year). Invalid values rejected."
    )


class SearchRequest(BaseSearchRequest):
    """
    Complete search request model for Brave Search Web API.

    Supports all available Brave Search parameters with full type validation
    and descriptions for LLM tool understanding.
    """

    safesearch: Optional[Literal["off", "moderate", "strict"]] = Field(
        default="moderate",
        description="Content filtering level: 'off', 'moderate' (default), or 'strict'."
    )

    result_filter: Optional[str] = Field(
        default=None,
        description="Comma-separated result types to filter by: 'discussions', 'faq', 'infobox', 'news', 'videos', 'images', etc. Leave empty to include all types."
    )

    units: Optional[Literal["imperial", "metric"]] = Field(
        default=None,
        description="Measurement system for results: 'imperial' or 'metric'. Leave empty for system default."
    )

    goggles: Optional[str] = Field(
        default=None,
        description="Custom re-ranking Goggle URL or definition (up to 3 supported). Used for custom result ranking logic."
    )

    extra_snippets: Optional[bool] = Field(
        default=False,
        description="Retrieve additional alternative excerpts/snippets from each result. Defaults to False."
    )

    summary: Optional[bool] = Field(
        default=False,
        description="Enable AI-generated summary of top results. Defaults to False."
    )

    enable_rich_callback: Optional[bool] = Field(
        default=False,
        description="Enable real-time rich results via callback URL (advanced). Defaults to False."
    )

    include_fetch_metadata: Optional[bool] = Field(
        default=False,
        description="Include fetch metadata in response (headers, response time, etc.). Defaults to False."
    )

    operators: Optional[bool] = Field(
        default=True,
        description="Apply search operators to query (e.g., site:, filetype:). Defaults to True."
    )


class SearchResult(BaseModel):
    """Single search result from Brave Search API"""

    title: str = Field(..., description="Result title/headline")
    url: str = Field(..., description="Result URL")
    description: str = Field(..., description="Result snippet/description")
    source: Optional[str] = Field(default=None, description="Source domain or type")


class SearchResponse(BaseModel):
    """Complete search response containing all results and metadata"""

    results: list[SearchResult]
    query: str
    count: int
    offset: int
    took_ms: Optional[int] = None


class NewsSearchRequest(BaseSearchRequest):
    """
    News search request model for Brave Search News API.

    Inherits common search parameters from BaseSearchRequest.
    News-specific defaults: freshness defaults to 'pw' (past week) for relevance.
    """

    freshness: Optional[Literal["pd", "pw", "pm", "py"]] = Field(
        default="pw",
        description="Filter by news age. MUST be one of: 'pd' (past day), 'pw' (past week, default), 'pm' (past month), 'py' (past year)."
    )


def search_web(request: SearchRequest) -> SearchResponse:
    """
    Execute web search using Brave Search API with comprehensive filtering and parameter support.

    Args:
        request: SearchRequest object containing query and all optional parameters

    Returns:
        SearchResponse with list of SearchResult objects, query metadata

    Raises:
        httpx.HTTPError: If API request fails
        ValueError: If query is invalid or API returns error

    Example:
        # Basic search
        request = SearchRequest(q="python async programming")
        response = search_web(request)

        # Search with filtering
        request = SearchRequest(
            q="machine learning",
            count=10,
            safesearch="strict",
            freshness="pm",  # past month only
            country="US"
        )
        response = search_web(request)

        # Search news results only
        request = SearchRequest(
            q="AI news",
            result_filter="news",
            freshness="pd",  # today's news
            count=15
        )
        response = search_web(request)
    """

    settings = Settings()
    api_key = settings.brave_search_api_key

    if not api_key:
        raise ValueError("BRAVE_SEARCH_API_KEY not configured in settings")

    # Build query parameters from request model
    params = request.model_dump(exclude_none=True)

    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
    }

    logger.info("Executing web search", query=request.q, count=request.count, safesearch=request.safesearch)

    try:
        with httpx.Client() as client:
            response = client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params=params,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()

            data = response.json()

            # Parse results from 'web' section (primary results)
            results = []
            web_results = data.get("web", [])

            # Handle if web_results is a dict with 'results' key
            if isinstance(web_results, dict):
                web_results = web_results.get("results", [])

            for result in web_results:
                if isinstance(result, dict):
                    results.append(SearchResult(
                        title=result.get("title", ""),
                        url=result.get("url", ""),
                        description=result.get("description", ""),
                        source=result.get("type", "web")
                    ))

            logger.info("Search complete", query=request.q, result_count=len(results))

            return SearchResponse(
                results=results,
                query=request.q,
                count=len(results),
                offset=request.offset,
                took_ms=data.get("took_ms")
            )

    except httpx.HTTPError as e:
        logger.error("Search API error", error=str(e), query=request.q)
        raise ValueError(f"Search API error: {e}") from e


def search_news(request: NewsSearchRequest) -> SearchResponse:
    """
    Execute news search using Brave Search News API with news-specific filtering.

    Args:
        request: NewsSearchRequest object containing query and news-specific parameters

    Returns:
        SearchResponse with list of SearchResult objects filtered for news

    Raises:
        httpx.HTTPError: If API request fails
        ValueError: If query is invalid or API returns error

    Example:
        # Search latest AI news
        request = NewsSearchRequest(q="artificial intelligence", freshness="pw")
        response = search_news(request)

        # Search news from specific country
        request = NewsSearchRequest(
            q="tech news",
            country="GB",
            freshness="pd"
        )
        response = search_news(request)
    """

    settings = Settings()
    api_key = settings.brave_search_api_key

    if not api_key:
        raise ValueError("BRAVE_SEARCH_API_KEY not configured in settings")

    # Build query parameters from request model
    params = request.model_dump(exclude_none=True)

    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
    }

    logger.info("Executing news search", query=request.q, count=request.count)

    try:
        with httpx.Client() as client:
            response = client.get(
                "https://api.search.brave.com/res/v1/news/search",
                params=params,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()

            data = response.json()

            # Parse news results
            results = []
            news_results = data.get("results", [])

            for result in news_results:
                if isinstance(result, dict):
                    results.append(SearchResult(
                        title=result.get("title", ""),
                        url=result.get("url", ""),
                        description=result.get("description", ""),
                        source=result.get("source", {}).get("name", "news") if isinstance(result.get("source"), dict) else result.get("source", "news")
                    ))

            logger.info("News search complete", query=request.q, result_count=len(results))

            return SearchResponse(
                results=results,
                query=request.q,
                count=len(results),
                offset=request.offset
            )

    except httpx.HTTPError as e:
        logger.error("News search API error", error=str(e), query=request.q)
        raise ValueError(f"News search API error: {e}") from e


if __name__ == "__main__":
    # Test basic web search
    request = SearchRequest(q="Python async programming", count=5)
    response = search_web(request)
    print(f"\nWeb Search - Query: {response.query}")
    print(f"Results: {response.count}\n")
    for result in response.results:
        print(f"Title: {result.title}")
        print(f"URL: {result.url}")
        print(f"Description: {result.description}\n")

    # Test news search
    print("\n--- News Search (AI News, Past Week) ---")
    request = NewsSearchRequest(
        q="artificial intelligence",
        freshness="pw",
        count=5
    )
    response = search_news(request)
    print(f"Query: {response.query}")
    print(f"Results: {response.count}\n")
    for result in response.results:
        print(f"Title: {result.title}")
        print(f"Source: {result.source}")
        print(f"URL: {result.url}")
        print()
