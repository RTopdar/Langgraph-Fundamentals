from langchain_openrouter import ChatOpenRouter
from settings import Settings


def get_model() -> ChatOpenRouter:
    """Get configured LLM instance"""
    settings = Settings()
    return ChatOpenRouter(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        temperature=0.7,
        max_retries=3,
    )


if __name__ == "__main__":
    model = get_model()
    messages = [
        (
            "system",
            "You are a helpful assistant that translates English to French. Translate the user sentence.",
        ),
        ("human", "I love programming."),
    ]
    ai_msg = model.invoke(messages)
    print(ai_msg.content)
