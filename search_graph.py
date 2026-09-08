"""
LangGraph Search Agent using Brave Search Tool

Demonstrates how to use the search_tool with LangGraph to build a multi-turn
search-capable agent that can fetch and reason over search results.
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, ToolMessage
from langsmith import traceable
import json
from datetime import datetime
from langgraph.checkpoint.memory import MemorySaver

from model_config import get_model
from logging_config import setup_logging, get_logger
from search_tool import search_web, search_news, SearchRequest, NewsSearchRequest
from settings import Settings
import os

setup_logging()
logger = get_logger(__name__)
memory = MemorySaver()

# Configure LangSmith from settings
settings = Settings()
if settings.langsmith_api_key:
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    logger.info("LangSmith tracing enabled", project=settings.langsmith_project)

model = get_model()

# Get current date for context
CURRENT_DATE = datetime.now().strftime("%B %d, %Y")
CURRENT_YEAR = datetime.now().year


class State(TypedDict):
    messages: Annotated[list, add_messages]
    search_results: Annotated[list, lambda x, y: y]


# Define web search as a tool that LLM can call
@tool
@traceable
def web_search(
    query: str,
    count: int = 5,
    safesearch: str = "moderate",
    freshness: str = None,
    country: str = "US",
) -> str:
    """
    Search the web using Brave Search API with flexible filtering and parameters.

    This tool searches across all web content, webpages, and general internet resources.
    Perfect for finding information, articles, documentation, and general web content.

    Args:
        query: Search query (max 400 characters, 50 words)
        count: Number of results (1-20, default 5)
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
            count=min(count, 5),
            safesearch=safesearch,
            freshness=freshness,
            country=country,
        )
        response = search_web(request)

        # Format results for LLM consumption
        formatted_results = []
        for result in response.results:
            formatted_results.append(
                {
                    "title": result.title,
                    "url": result.url,
                    "description": result.description,
                    "source": result.source,
                }
            )

        return json.dumps(
            {
                "query": response.query,
                "count": response.count,
                "results": formatted_results,
            },
            indent=2,
        )
    except Exception as e:
        logger.error("Web search tool error", error=str(e), query=query)
        return json.dumps({"error": str(e), "query": query}, indent=2)


@tool
@traceable
def news_search(
    query: str, count: int = 5, freshness: str = "pw", country: str = "US"
) -> str:
    """
    Search news using Brave Search News API with news-specific filtering.

    This tool searches exclusively in news content, articles from news sources,
    and recently published news stories. Ideal for finding current events and recent developments.

    Args:
        query: News search query (max 400 characters, 50 words)
        count: Number of news results (1-20, default 5)
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
            q=query, count=min(count, 5), freshness=freshness, country=country
        )
        response = search_news(request)

        # Format news results for LLM consumption
        formatted_results = []
        for result in response.results:
            formatted_results.append(
                {
                    "title": result.title,
                    "url": result.url,
                    "description": result.description,
                    "source": result.source,
                }
            )

        return json.dumps(
            {
                "query": response.query,
                "count": response.count,
                "results": formatted_results,
            },
            indent=2,
        )
    except Exception as e:
        logger.error("News search tool error", error=str(e), query=query)
        return json.dumps({"error": str(e), "query": query}, indent=2)


# Tools for agent
tools = [web_search, news_search]
tool_node = ToolNode(tools)

graph_builder = StateGraph(State)

logger.info("Graph builder initialized")


@traceable(name="agent_node")
def agent(state: State):
    """Main agent node that processes messages and decides to search or respond"""
    logger.info(
        "Agent node invoked",
        messages_count=len(state["messages"]),
        search_results_count=len(state.get("search_results", [])),
    )
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
    if messages and (
        not isinstance(messages[0], dict)
        or (isinstance(messages[0], dict) and messages[0].get("type") != "system")
    ):
        messages = [{"type": "system", "content": system_context}] + messages

    # Bind tools to model
    model_with_tools = model.bind_tools(tools)
    response = model_with_tools.invoke(messages)

    logger.info(
        "LLM response",
        response_type=type(response).__name__,
        has_content=bool(getattr(response, "content", None)),
    )
    if hasattr(response, "content"):
        logger.info("LLM content", content=response.content)

    has_tool_calls = hasattr(response, "tool_calls") and bool(response.tool_calls)
    logger.info(
        "Agent response",
        tool_calls=has_tool_calls,
        tool_calls_count=(
            len(response.tool_calls) if hasattr(response, "tool_calls") else 0
        ),
    )
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tool_call in response.tool_calls:
            tc_id = tool_call.get("id") if isinstance(tool_call, dict) else tool_call.id
            tc_name = (
                tool_call.get("name") if isinstance(tool_call, dict) else tool_call.name
            )
            tc_args = (
                tool_call.get("args")
                if isinstance(tool_call, dict)
                else getattr(tool_call, "args", {})
            )
            logger.info("Tool call", id=tc_id, name=tc_name, args=tc_args)

    return {"messages": [response]}


@traceable(name="process_tool_result_node")
def process_tool_result(state: State):
    """Extract search results from tool messages and populate state"""
    logger.info(
        "Process tool result node invoked",
        messages_count=len(state["messages"]),
        current_search_results=len(state.get("search_results", [])),
    )
    messages = state["messages"]
    search_results = []

    for msg in reversed(messages):
        if not isinstance(msg, ToolMessage):
            break

        try:
            logger.info(
                "Processing tool result",
                tool_call_id=msg.tool_call_id,
                tool_name=msg.name,
            )

            if not msg.content or not msg.content.strip():
                logger.debug(
                    "Empty tool result, skipping", tool_call_id=msg.tool_call_id
                )
                continue

            payload = json.loads(msg.content)
            if "error" in payload:
                logger.error(
                    "Tool error in message",
                    tool_call_id=msg.tool_call_id,
                    error=payload["error"],
                )
                continue

            if "results" in payload:
                logger.info(
                    "Tool results extracted",
                    tool_call_id=msg.tool_call_id,
                    result_count=len(payload["results"]),
                )
                search_results.extend(payload["results"])
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            logger.error(
                "Failed to parse tool result",
                tool_call_id=msg.tool_call_id,
                error=str(e),
                content=repr(msg.content) if hasattr(msg, "content") else "N/A",
            )

    return {"search_results": search_results}


# Add nodes
graph_builder.add_node("agent", agent)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("process_tool_result", process_tool_result)


# Add edges
def log_routing(state: State):
    """Debug routing decisions"""
    logger.info(
        "Routing state",
        messages_count=len(state["messages"]),
        search_results_count=len(state.get("search_results", [])),
    )
    if state["messages"]:
        last_msg = state["messages"][-1]
        has_calls = hasattr(last_msg, "tool_calls") and bool(last_msg.tool_calls)
        logger.debug(
            "Routing decision",
            has_tool_calls=has_calls,
            message_type=type(last_msg).__name__,
        )


@traceable(name="tool_approval_node")
def tool_approval_node(state: State):
    """Show tool calls awaiting approval"""
    last_msg = state["messages"][-1]
    tool_calls = last_msg.tool_calls if hasattr(last_msg, "tool_calls") else []

    # Format tool calls for review
    tool_info = []
    for tc in tool_calls:
        tc_name = tc.get("name") if isinstance(tc, dict) else tc.name
        tc_args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {})
        tool_info.append({"name": tc_name, "args": tc_args})

    logger.info(
        "Interrupt: tool approval required",
        tool_calls_count=len(tool_calls),
        tools=[t["name"] for t in tool_info]
    )

    # Display tools for approval
    print("\n" + "="*80)
    print("TOOL APPROVAL REQUIRED (Execution paused)")
    print("="*80)
    for i, tool in enumerate(tool_info, 1):
        print(f"\n{i}. Tool: {tool['name']}")
        print(f"   Args: {tool['args']}")
    print("\n" + "="*80)
    print("Resume to approve, or rewind to reject.\n")

    return {"messages": []}


def route_after_agent(state: State) -> str:
    """Route to approval or tools based on agent response"""
    if not state["messages"]:
        return END

    last_msg = state["messages"][-1]
    has_tool_calls = hasattr(last_msg, "tool_calls") and bool(last_msg.tool_calls)

    if has_tool_calls:
        return "tool_approval"

    return END


# Add nodes
graph_builder.add_node("tool_approval", tool_approval_node)

# Add edges
graph_builder.add_edge(START, "agent")
graph_builder.add_conditional_edges(
    "agent", route_after_agent, {"tool_approval": "tool_approval", "__end__": END}
)
graph_builder.add_edge("tool_approval", "tools")
graph_builder.add_edge("tools", "process_tool_result")
graph_builder.add_edge("process_tool_result", "agent")

graph = graph_builder.compile(
    checkpointer=memory,
    name="search_graph",
    interrupt_before=["tools"]
)

config = {
    "configurable":{
        "thread_id": "1"
    }
}

logger.info("Search graph compiled successfully")


if __name__ == "__main__":
    logger.info("Starting search graph with interrupt_before")

    user_query = "What are the latest developments in LLM reasoning? I also need to know when was fable 5.1 released"
    logger.info("Query", query=user_query)

    initial_input = {"messages": [("user", user_query)]}

    while True:
        logger.info("Invoking graph")
        result = graph.invoke(initial_input, config=config)

        # Get current state to check if interrupted
        state = graph.get_state(config)

        print(f"\nCurrent next node(s): {state.next}")

        if state.next and state.next[0] == "tools":
            # Execution paused before tools
            print("\n" + "="*80)
            print("EXECUTION PAUSED BEFORE TOOLS")
            print("="*80)

            last_msg = result["messages"][-1]
            if hasattr(last_msg, "tool_calls"):
                for i, tc in enumerate(last_msg.tool_calls, 1):
                    tc_name = tc.get("name") if isinstance(tc, dict) else tc.name
                    tc_args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {})
                    print(f"\n{i}. {tc_name}")
                    print(f"   Args: {tc_args}")

            approval = input("\nApprove tool execution? (yes/no): ").strip().lower()

            if approval in ["yes", "y"]:
                logger.info("User approved - resuming")
                initial_input = None
                continue
            else:
                logger.info("User rejected - aborting")
                break

        # Execution completed (no more interrupts)
        print("\n" + "="*80)
        print("EXECUTION COMPLETE")
        print("="*80 + "\n")

        final_message = result["messages"][-1]
        if hasattr(final_message, "content"):
            logger.info(
                "Agent response received",
                response_length=len(final_message.content)
            )
            print(f"Agent Response:\n{final_message.content}\n")

        # Show checkpoint history
        print("\n" + "="*80)
        print("CHECKPOINT HISTORY")
        print("="*80 + "\n")

        checkpoints = list(graph.get_state_history(config))
        for i, checkpoint in enumerate(checkpoints):
            print(f"Checkpoint {i}:")
            print(f"  Next: {checkpoint.next}")
            print(f"  Messages: {len(checkpoint.values.get('messages', []))}")
            print(f"  Search results: {len(checkpoint.values.get('search_results', []))}")
            print()

        break

    # # Test 2: Search with specific parameters
    # logger.info("Test 2: Filtered Search (Recent Results)")
    # user_query = "Tell me about quantum computing breakthroughs this week"
    # logger.info("Query", query=user_query)

    # result = graph.invoke({"messages": [("user", user_query)]})
    # final_message = result["messages"][-1]

    # if hasattr(final_message, "content"):
    #     logger.info(
    #         "Agent response received", response_length=len(final_message.content)
    #     )
    #     print(f"\n{'='*80}\nTest 2 Response:\n{'='*80}\n{final_message.content}\n{'='*80}")

    # # Test 3: Multi-turn conversation
    # logger.info("Test 3: Multi-turn Conversation")
    # messages = [
    #     ("user", "Search for Python async programming best practices"),
    #     (
    #         "assistant",
    #         "I'll search for Python async programming best practices for you.",
    #     ),
    # ]

    # logger.info("Starting multi-turn conversation")
    # result = graph.invoke({"messages": messages})

    # if result["messages"]:
    #     final_message = result["messages"][-1]
    #     if hasattr(final_message, "content"):
    #         logger.info(
    #             "Multi-turn conversation complete",
    #             response_length=len(final_message.content),
    #         )
    #         print(
    #             f"\n{'='*80}\nTest 3 Response:\n{'='*80}\n{final_message.content}\n{'='*80}"
    #         )

try:
    png_bytes = graph.get_graph().draw_mermaid_png()
    with open("graph.png", "wb") as f:
        f.write(png_bytes)
except Exception as e:
    print("Error displaying graph:", e)
