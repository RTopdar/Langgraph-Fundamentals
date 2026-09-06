"""
LangGraph Search Agent using Brave Search Tool

Demonstrates how to use the search_tool with LangGraph to build a multi-turn
search-capable agent that can fetch and reason over search results.
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
import json
from datetime import datetime

from model_config import get_model
from logging_config import setup_logging, get_logger
from search_tool import search_web, search_news, SearchRequest, NewsSearchRequest

setup_logging()
logger = get_logger(__name__)

model = get_model()

# Get current date for context
CURRENT_DATE = datetime.now().strftime("%B %d, %Y")
CURRENT_YEAR = datetime.now().year


class State(TypedDict):
    messages: Annotated[list, add_messages]
    search_results: Annotated[list, lambda x, y: y]


# Define web search as a tool that LLM can call
@tool
def web_search(
    query: str,
    count: int = 10,
    safesearch: str = "moderate",
    freshness: str = None,
    country: str = "US"
) -> str:
    """
    Search the web using Brave Search API with flexible filtering and parameters.

    This tool searches across all web content, webpages, and general internet resources.
    Perfect for finding information, articles, documentation, and general web content.

    Args:
        query: Search query (max 400 characters, 50 words)
        count: Number of results (1-20, default 10)
        safesearch: Content filtering - 'off', 'moderate' (default), 'strict'
        freshness: Filter by age - 'pd' (past day), 'pw' (past week), 'pm' (past month), 'py' (past year)
        country: Geographic region (2-letter code, default 'US')

    Returns:
        JSON string with search results containing title, url, description, and source

    Examples:
        web_search("python async programming")
        web_search("latest AI research", freshness="pm", country="US")
        web_search("machine learning libraries", count=15, safesearch="strict")
    """
    try:
        request = SearchRequest(
            q=query,
            count=min(count, 20),
            safesearch=safesearch,
            freshness=freshness,
            country=country
        )
        response = search_web(request)

        # Format results for LLM consumption
        formatted_results = []
        for result in response.results:
            formatted_results.append({
                "title": result.title,
                "url": result.url,
                "description": result.description,
                "source": result.source
            })

        return json.dumps({
            "query": response.query,
            "count": response.count,
            "results": formatted_results
        })
    except Exception as e:
        logger.error("Web search tool error", error=str(e), query=query)
        return json.dumps({"error": str(e), "query": query})


@tool
def news_search(
    query: str,
    count: int = 10,
    freshness: str = "pw",
    country: str = "US"
) -> str:
    """
    Search news using Brave Search News API with news-specific filtering.

    This tool searches exclusively in news content, articles from news sources,
    and recently published news stories. Ideal for finding current events and recent developments.

    Args:
        query: News search query (max 400 characters, 50 words)
        count: Number of news results (1-20, default 10)
        freshness: Filter by news age - 'pd' (past day), 'pw' (past week, default), 'pm' (past month), 'py' (past year)
        country: Geographic region (2-letter code, default 'US')

    Returns:
        JSON string with news results containing title, url, description, and news source

    Examples:
        news_search("artificial intelligence")
        news_search("quantum computing breakthroughs", freshness="pw")
        news_search("tech industry updates", country="GB", freshness="pd")
    """
    try:
        request = NewsSearchRequest(
            q=query,
            count=min(count, 20),
            freshness=freshness,
            country=country
        )
        response = search_news(request)

        # Format news results for LLM consumption
        formatted_results = []
        for result in response.results:
            formatted_results.append({
                "title": result.title,
                "url": result.url,
                "description": result.description,
                "source": result.source
            })

        return json.dumps({
            "query": response.query,
            "count": response.count,
            "results": formatted_results
        })
    except Exception as e:
        logger.error("News search tool error", error=str(e), query=query)
        return json.dumps({"error": str(e), "query": query})


# Tools for agent
tools = [web_search, news_search]
tool_node = ToolNode(tools)

graph_builder = StateGraph(State)

logger.info("Graph builder initialized")


def should_search(state: State) -> str:
    """Router that decides if agent should use search or respond directly"""
    last_message = state["messages"][-1]

    # If model called a tool, route to tool_node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Otherwise end conversation
    return "end"


def agent(state: State):
    """Main agent node that processes messages and decides to search or respond"""
    messages = state["messages"]

    # Inject date context if not already present
    system_context = f"""You are a helpful search assistant with access to web search and news search tools.

IMPORTANT CONTEXT:
- Today's date: {CURRENT_DATE}
- Current year: {CURRENT_YEAR}

When users ask for recent/latest/this week/this month information:
- "this week" → use freshness='pw' (past week)
- "this month" → use freshness='pm' (past month)
- "this year" or recent → use freshness='py' (past year)
- "today" or "this week" → use freshness='pd' (past day)

Always use these exact freshness values: 'pd' (past day), 'pw' (past week), 'pm' (past month), 'py' (past year).

When you infer dates in queries, use {CURRENT_YEAR} as the current year. Never assume old years.
Use the appropriate search tool:
- Use 'web_search' for general information, research, articles, documentation
- Use 'news_search' for current events, breaking news, recent developments"""

    # Check if first message is user message (not system message)
    if messages and not isinstance(messages[0], dict) or (isinstance(messages[0], dict) and messages[0].get("type") != "system"):
        messages = [{"type": "system", "content": system_context}] + messages

    # Bind tools to model
    model_with_tools = model.bind_tools(tools)
    response = model_with_tools.invoke(messages)

    logger.info("Agent response", tool_calls=hasattr(response, "tool_calls"))

    return {"messages": [response]}


def process_tool_result(state: State):
    """Process tool results and return to agent for further reasoning"""
    return state


# Add nodes
graph_builder.add_node("agent", agent)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("process_tool_result", process_tool_result)

# Add edges
graph_builder.add_edge(START, "agent")
graph_builder.add_conditional_edges(
    "agent",
    should_search,
    {
        "tools": "tools",
        "end": END
    }
)
graph_builder.add_edge("tools", "process_tool_result")
graph_builder.add_edge("process_tool_result", "agent")

graph = graph_builder.compile()

logger.info("Search graph compiled successfully")


if __name__ == "__main__":
    logger.info("Starting search graph tests")

    # Test 1: Simple search query
    logger.info("Test 1: Simple Search Query")
    user_query = "What are the latest developments in LLM reasoning?"
    logger.info("Query", query=user_query)

    result = graph.invoke({"messages": [("user", user_query)]})
    final_message = result["messages"][-1]

    if hasattr(final_message, "content"):
        logger.info("Agent response received", response_length=len(final_message.content))

    # Test 2: Search with specific parameters
    logger.info("Test 2: Filtered Search (Recent Results)")
    user_query = "Tell me about quantum computing breakthroughs this week"
    logger.info("Query", query=user_query)

    result = graph.invoke({"messages": [("user", user_query)]})
    final_message = result["messages"][-1]

    if hasattr(final_message, "content"):
        logger.info("Agent response received", response_length=len(final_message.content))

    # Test 3: Multi-turn conversation
    logger.info("Test 3: Multi-turn Conversation")
    messages = [
        ("user", "Search for Python async programming best practices"),
        ("assistant", "I'll search for Python async programming best practices for you."),
    ]

    logger.info("Starting multi-turn conversation")
    result = graph.invoke({"messages": messages})

    if result["messages"]:
        final_message = result["messages"][-1]
        if hasattr(final_message, "content"):
            logger.info("Multi-turn conversation complete", response_length=len(final_message.content))
