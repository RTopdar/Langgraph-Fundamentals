import csv
import logging
from pathlib import Path
from typing import TypedDict, Literal
from langgraph.types import Command

logger = logging.getLogger(__name__)


class Email(TypedDict):
    email_id: str
    sender_email: str
    email_content: str
    source_type: str
    source_queue: str
    source_priority: str


class EmailReaderState(TypedDict):
    """State for email batch processing loop"""

    emails: list[Email]
    current_index: int
    current_email: Email | None
    is_done: bool


def load_emails_from_csv(csv_path: str | Path) -> list[Email]:
    """Load emails from CSV file. Expects columns: id, subject, body, sender, timestamp"""
    path = Path(csv_path)
    if not path.exists():
        logger.error(f"CSV file not found: {path}")
        return []

    emails = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = Email(
                    email_id=row["email_id"].strip(),
                    sender_email=row["sender_email"].strip(),
                    email_content=row["email_content"].strip(),
                    source_type=row["source_type"].strip(),
                    source_queue=row["source_queue"].strip(),
                    source_priority=row["source_priority"].strip(),
                )
                emails.append(email)
        logger.info(f"Loaded {len(emails)} emails from {path}")
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        return []

    return emails


def email_reader_init(state: EmailReaderState) -> Command[Literal["classify", "end"]]:
    """Initialize email reader: load CSV, set first email, route to classification"""
    if not state["emails"]:
        logger.warning("No emails loaded in state")
        return Command(update={"is_done": True}, goto="end")

    if state["current_index"] >= len(state["emails"]):
        logger.info("All emails processed")
        return Command(update={"is_done": True}, goto="end")

    current_email = state["emails"][state["current_index"]]
    logger.info(
        f"Processing email {state['current_index'] + 1}/{len(state['emails'])}: {current_email['email_id']}"
    )

    return Command(update={"current_email": current_email}, goto="classify")


def email_reader_advance(
    state: EmailReaderState,
) -> Command[Literal["classify", "end"]]:
    """Advance to next email after classification is complete"""
    next_index = state["current_index"] + 1

    if next_index >= len(state["emails"]):
        logger.info("All emails processed")
        return Command(
            update={
                "current_index": next_index,
                "current_email": None,
                "is_done": True,
            },
            goto="end",
        )

    next_email = state["emails"][next_index]
    logger.info(
        f"Processing email {next_index + 1}/{len(state['emails'])}: {next_email['email_id']}"
    )

    return Command(
        update={"current_index": next_index, "current_email": next_email},
        goto="classify",
    )
