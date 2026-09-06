from settings import Settings
from logging_config import setup_logging, get_logger


def main():
    settings = Settings()
    setup_logging(settings.log_level)
    logger = get_logger(__name__)

    logger.info("Starting application", app_name=settings.app_name)
    logger.info("LLM configured", model=settings.openrouter_model)


if __name__ == "__main__":
    main()
