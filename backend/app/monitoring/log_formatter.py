"""Structured JSON log formatter."""

import json
import logging
from contextvars import ContextVar
from datetime import datetime

# Shared ContextVar for trace_id — set by TraceIDMiddleware
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)

# LogRecord attributes that should NOT be merged as extras
_RESERVED_ATTRS = frozenset({
    "args", "created", "exc_info", "exc_text", "filename", "funcName",
    "levelname", "levelno", "lineno", "message", "module", "msecs", "msg",
    "name", "pathname", "process", "processName", "relativeCreated",
    "stack_info", "taskName", "thread", "threadName",
})


class StructuredLogFormatter(logging.Formatter):
    """Format log records as single-line JSON with consistent fields."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "func": record.funcName,
            "message": record.getMessage(),
        }

        # Include trace_id from contextvars if available
        tid = trace_id_var.get(None)
        if tid:
            entry["trace_id"] = tid

        # Merge extra fields (anything not in reserved set or already in entry)
        for key, val in record.__dict__.items():
            if key not in _RESERVED_ATTRS and key not in entry:
                entry[key] = val

        # Include exception traceback
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=str)
