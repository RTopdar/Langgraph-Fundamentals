import sys
import structlog
import json


def format_json_fields(logger, name, event_dict):
    """Format dict values as pretty-printed JSON for readability"""
    for key, value in event_dict.items():
        if isinstance(value, (dict, list)):
            event_dict[key] = "\n" + json.dumps(value, indent=2)
    return event_dict


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structlog with colorful output"""

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            format_json_fields,
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(__import__("logging"), log_level)
        ),
    )

    # Configure standard library logging
    import logging

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level),
    )


def get_logger(name: str = __name__):
    """Get a configured logger instance"""
    return structlog.get_logger(name)
