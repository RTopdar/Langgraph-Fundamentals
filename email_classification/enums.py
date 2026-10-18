from enum import Enum
from typing import TypedDict, Optional

from pydantic import BaseModel


# TypeSafe primitives for system-one judgments
class TypeSafeChoice(TypedDict):
    """Choice primitive: select one from defined options"""

    choice: str
    probabilities: dict[str, float]
    confidence: float


class TypeSafeNoul(TypedDict):
    """Noul primitive: yes/no probability (0-1)"""

    noul: float


class TypeSafeScore(TypedDict):
    """Score primitive: position on ordered spectrum"""

    score: float
    confidence: float
    probabilities: dict[str, float]
    legend: dict[str, str]


# Email classification enums
class Intent(str, Enum):
    QUESTION = "question"
    BUG = "bug"
    BILLING = "billing"
    FEATURE = "feature"
    COMPLEX = "complex"


INTENT_DEFINITIONS = {
    "question": "User asking for help, clarification, or information",
    "bug": "Report of a defect, error, or unexpected behavior",
    "billing": "Payment, subscription, or billing-related inquiry",
    "feature": "Request for a new feature or product enhancement",
    "complex": "Multi-faceted issue requiring coordination or escalation",
}


class Urgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


URGENCY_DEFINITIONS = {
    "low": "Non-urgent, can be addressed in regular workflow",
    "medium": "Standard priority, should be addressed within normal timeframe",
    "high": "Time-sensitive, requires prompt attention",
    "critical": "Emergency requiring immediate action, may impact service or customers",
}


class EmailClassification(BaseModel):
    intent: Intent
    intent_confidence: float
    urgency: Urgency
    urgency_confidence: float
    topic: str
    summary: str


class EmailAgentState(TypedDict, total=False):
    """State for email classification graph. Uses TypedDict for LangGraph compatibility."""

    emails: list[dict]
    current_index: int
    email_content: str
    sender_email: str
    email_id: str
    classification: EmailClassification | None
    search_results: list[str]
    customer_history: dict
    draft_response: str
    messages: list[str]
    current_email: dict | None
    is_done: bool
