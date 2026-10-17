import json
import logging
import sys
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record):
        evento = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=UTC
            ).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "path": getattr(record, "path", None),
            "status_code": getattr(record, "status_code", None),
            "method": getattr(record, "method", None),
            "duration_ms": getattr(record, "duration_ms", None),
        }

        return json.dumps(evento, ensure_ascii=False)


def configurar_logger():
    logger = logging.getLogger("backlog.http")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    return logger