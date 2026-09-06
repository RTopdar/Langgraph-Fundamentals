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
import json

from model_config import get_model
from logging_config import setup_logging, get_logger
from search_tool import search_web, search_news, SearchRequest, NewsSearchRequest

setup_logging()
logger = get_logger(__name__)

model = get_model()


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
    print("\n" + "="*80)
    print("LangGraph Search Agent with Brave Search Tool")
    print("="*80 + "\n")

    # Test 1: Simple search query
    print("Test 1: Simple Search Query")
    print("-" * 40)
    user_query = "What are the latest developments in LLM reasoning?"
    print(f"Query: {user_query}\n")

    result = graph.invoke({"messages": [("user", user_query)]})
    final_message = result["messages"][-1]

    if hasattr(final_message, "content"):
        print(f"Agent Response:\n{final_message.content}\n")

    # Test 2: Search with specific parameters
    print("\nTest 2: Filtered Search (Recent Results)")
    print("-" * 40)
    user_query = "Tell me about quantum computing breakthroughs this week"
    print(f"Query: {user_query}\n")

    result = graph.invoke({"messages": [("user", user_query)]})
    final_message = result["messages"][-1]

    if hasattr(final_message, "content"):
        print(f"Agent Response:\n{final_message.content}\n")

    # Test 3: Multi-turn conversation
    print("\nTest 3: Multi-turn Conversation")
    print("-" * 40)
    messages = [
        ("user", "Search for Python async programming best practices"),
        ("assistant", "I'll search for Python async programming best practices for you."),
    ]

    print("Initial query: Search for Python async programming best practices\n")
    result = graph.invoke({"messages": messages})

    if result["messages"]:
        final_message = result["messages"][-1]
        if hasattr(final_message, "content"):
            print(f"Agent Response:\n{final_message.content}\n")
