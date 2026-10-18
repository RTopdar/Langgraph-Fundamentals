import logging
from typing import TypedDict
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from email_classification.enums import (
    Intent,
    Urgency,
    EmailClassification,
    INTENT_DEFINITIONS,
    URGENCY_DEFINITIONS,
)
from settings import Settings

settings = Settings()
from langchain_typesafe import Choice, Noul, Score, TypeSafeClassifier

logger = logging.getLogger(__name__)


class IntentClassifierState(TypedDict):
    """State for intent classification node"""

    current_email: dict  # Email object with id, subject, body, sender, timestamp
    classification: EmailClassification | None


def intent_classifier(state: IntentClassifierState) -> dict:
    """
    Classify email intent using TypeSafe.

    Receives current_email from state, calls TypeSafe Choice primitive,
    maps result to Intent enum, returns partial state update.
    """
    email = state["current_email"]
    if not email:
        logger.warning("No current email in state")
        return {}

    logger.info(f"Classifying intent for email {email['email_id']}")

    try:
        logger.info(
            f"Creating TypeSafeClassifier with API key: {settings.typesafe_api_key[:10] if settings.typesafe_api_key else 'NONE'}..."
        )
        classifier = TypeSafeClassifier(api_key=settings.typesafe_api_key)
        logger.info("Classifier created successfully")

        classifier_state = email["email_content"]
        intent_criteria = {e.value: e.name for e in Intent}
        questions = {
            "intent": Choice(
                instructions=f"Read the email and determine the primary intent. Choose one: {', '.join(intent_criteria.keys())}",
                criteria=INTENT_DEFINITIONS,
            ),
            "urgency": Choice(
                instructions=f"Determine the urgency of the situation. Choose one: {', '.join([u.value for u in Urgency])}",
                criteria=URGENCY_DEFINITIONS,
            ),
        }

        logger.info("Calling classifier.invoke()...")

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        def invoke_with_retry():
            return classifier.invoke(
                {
                    "state": classifier_state,
                    "questions": questions,
                }
            )

        result = invoke_with_retry()
        logger.info(f"Got result: {result}")

        intent_result = result.choices["intent"]
        urgency_result = result.choices["urgency"]

        classification = EmailClassification(
            intent=Intent(intent_result.choice),
            intent_confidence=intent_result.confidence,
            urgency=Urgency(urgency_result.choice),
            urgency_confidence=urgency_result.confidence,
            topic="",
            summary="",
        )

        logger.info(
            f"Classification complete: intent={classification.intent}, urgency={classification.urgency}"
        )
        return {"classification": classification}
    except Exception as e:
        logger.error(f"Classifier error: {e}", exc_info=True)
        raise
