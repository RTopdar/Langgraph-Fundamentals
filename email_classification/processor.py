"""
Email classification graph processor.

Teaches LangGraph step-by-step: state flow, nodes, edges, compile, invoke.
"""

from langgraph.graph import StateGraph, START
from langgraph.types import Command
from email_classification.enums import EmailAgentState
from email_classification.node_tools.email_reader import (
    email_reader_init,
    email_reader_advance,
)
from langgraph.types import RetryPolicy
from langgraph.checkpoint.memory import MemorySaver
from settings import Settings
import logging

logging.basicConfig(
    level=getattr(logging, Settings().log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

# Step 1: Create the graph with state schema
# StateGraph tells LangGraph: "This graph uses EmailAgentState. Routes are defined below."
# Think: empty blueprint. No nodes yet.

graph = StateGraph(EmailAgentState)

# Step 2: Add nodes (functions that execute in the graph)
# graph.add_node(name, function)
# The function receives state, returns state update or Command.


def init_node(state: EmailAgentState) -> dict:
    """Load emails from CSV. First node in flow."""
    from email_classification.node_tools.email_reader import load_emails_from_csv

    if not state["emails"]:
        emails = load_emails_from_csv(
            "/home/rounak/Desktop/Projects/langgraph-learn/email_classification/dummy_emails.csv"
        )
        return {"emails": emails, "current_index": 0}

    return {}


graph.add_node("init", init_node)

# Step 3: Add email_reader_init node
# This node uses Command to route dynamically.
# It checks: more emails? goto "classify". All done? goto "end".


def reader_init_node(state: EmailAgentState):
    """Route to first email or end if no emails."""
    return email_reader_init(state)


graph.add_node("reader_init", reader_init_node)


def classify_node(state: EmailAgentState):
    """Classify current email intent and urgency."""
    from email_classification.node_tools.intent_classifier import intent_classifier

    return intent_classifier(state)


graph.add_node(
    "classify",
    classify_node,
    retry_policy=RetryPolicy(max_attempts=3, backoff_factor=2),
)


def reader_advance_node(state: EmailAgentState):
    """Advance to next email or end if done."""
    return email_reader_advance(state)


graph.add_node("reader_advance", reader_advance_node)
graph.add_node("end", lambda state: state)


graph.add_edge(START, "init")
graph.add_edge("init", "reader_init")

graph.add_edge("classify", "reader_advance")

memory = MemorySaver()
app = graph.compile(checkpointer=memory, name="email_classifier")


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "1"}}
    initial_state: EmailAgentState = {
        "email_content": "",
        "sender_email": "",
        "email_id": "",
        "emails": [],
        "current_index": 0,
        "classification": None,
        "search_results": None,
        "customer_history": None,
        "draft_response": None,
        "messages": None,
    }

    result = app.invoke(initial_state, config=config)
    logger.info(f"Graph completed. Final state: {result}")
