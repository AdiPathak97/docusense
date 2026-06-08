"""
Centralised logging configuration for DocuSense.

Call configure_logging() exactly once at application startup (in main.py) before
the FastAPI app is constructed, so any import-time log calls are already formatted.

Design decisions:
- Root logger is always WARNING — suppresses third-party noise (SQLAlchemy, httpx,
  chromadb client, anthropic SDK) regardless of LOG_LEVEL.
- The 'backend' logger inherits LOG_LEVEL so all app loggers (backend.api.*,
  backend.services.*, backend.agent.*) get the right verbosity without individual config.
- Stdout only — no file handler. Docker captures stdout; use the json-file logging
  driver in docker-compose.yml for rotation and persistence across restarts.
- LOG_FORMAT=json switches to a stdlib-only JSON formatter (no new dependency).
  Useful when feeding logs to a log aggregator or running in CI.
- request_id is stamped onto every LogRecord by the RequestIdFilter in main.py.
  The plain format includes %(request_id)s; it renders as "" on non-request log lines.
"""

import json
import logging
import logging.config


PLAIN_FORMAT = "%(asctime)s [%(levelname)s] %(name)s [%(request_id)s] — %(message)s"

_VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class _JsonFormatter(logging.Formatter):
    """Stdlib-only structured JSON formatter. No third-party dependencies."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", "")
        if request_id:
            log_obj["request_id"] = request_id
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def configure_logging(log_level: str = "INFO", log_format: str = "plain") -> None:
    """Configure the root and 'backend' loggers.

    Args:
        log_level: Verbosity for the 'backend.*' namespace.
                   One of DEBUG / INFO / WARNING / ERROR / CRITICAL.
                   Defaults to INFO. Validated and uppercased before use.
        log_format: 'plain' (human-readable) or 'json' (structured JSON).
                    Defaults to 'plain'.
    """
    level = log_level.upper()
    if level not in _VALID_LEVELS:
        level = "INFO"  # safe fallback; do not crash on a bad env var

    use_json = log_format.lower() == "json"

    if use_json:
        formatter_cfg: dict = {"()": "backend.logging_config._JsonFormatter"}
    else:
        formatter_cfg = {"format": PLAIN_FORMAT}

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": formatter_cfg,
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "default",
                },
            },
            "loggers": {
                # All backend.* loggers inherit this level and handler.
                "backend": {
                    "level": level,
                    "handlers": ["console"],
                    "propagate": False,
                },
            },
            "root": {
                # Third-party libraries: only WARNING and above.
                "level": "WARNING",
                "handlers": ["console"],
            },
        }
    )
