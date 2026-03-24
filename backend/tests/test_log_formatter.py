"""Unit tests for StructuredLogFormatter."""

import json
import logging
import pytest
from app.monitoring.log_formatter import StructuredLogFormatter, trace_id_var

REQUIRED_KEYS = {"timestamp", "level", "logger", "module", "func", "message"}


@pytest.fixture
def formatter():
    return StructuredLogFormatter()


def _make_record(msg="hello", level=logging.INFO, exc_info=None, extra=None):
    logger = logging.getLogger("test.module")
    record = logger.makeRecord(
        name="test.module",
        level=level,
        fn="test_file.py",
        lno=42,
        msg=msg,
        args=(),
        exc_info=exc_info,
    )
    if extra:
        for k, v in extra.items():
            setattr(record, k, v)
    return record


def test_valid_json_output(formatter):
    record = _make_record("test message")
    output = formatter.format(record)
    parsed = json.loads(output)
    assert isinstance(parsed, dict)


def test_required_keys_present(formatter):
    record = _make_record("test message")
    output = formatter.format(record)
    parsed = json.loads(output)
    assert REQUIRED_KEYS.issubset(parsed.keys())


def test_message_matches(formatter):
    record = _make_record("specific message")
    parsed = json.loads(formatter.format(record))
    assert parsed["message"] == "specific message"


def test_level_matches(formatter):
    record = _make_record(level=logging.WARNING)
    parsed = json.loads(formatter.format(record))
    assert parsed["level"] == "WARNING"


def test_iso8601_timestamp(formatter):
    record = _make_record()
    parsed = json.loads(formatter.format(record))
    ts = parsed["timestamp"]
    # ISO 8601 with milliseconds: YYYY-MM-DDTHH:MM:SS.mmm
    assert "T" in ts
    assert "." in ts
    parts = ts.split(".")
    assert len(parts[1]) == 3  # millisecond precision


def test_exception_field_when_exc_info(formatter):
    try:
        raise ValueError("boom")
    except ValueError:
        import sys
        record = _make_record(exc_info=sys.exc_info())
    parsed = json.loads(formatter.format(record))
    assert "exception" in parsed
    assert "ValueError" in parsed["exception"]
    assert "boom" in parsed["exception"]


def test_no_exception_field_without_exc_info(formatter):
    record = _make_record()
    parsed = json.loads(formatter.format(record))
    assert "exception" not in parsed


def test_extra_dict_merged(formatter):
    record = _make_record(extra={"request_id": "abc123", "user": "test"})
    parsed = json.loads(formatter.format(record))
    assert parsed["request_id"] == "abc123"
    assert parsed["user"] == "test"


def test_trace_id_included_when_set(formatter):
    token = trace_id_var.set("trace-abc-123")
    try:
        record = _make_record()
        parsed = json.loads(formatter.format(record))
        assert parsed["trace_id"] == "trace-abc-123"
    finally:
        trace_id_var.reset(token)


def test_trace_id_absent_when_not_set(formatter):
    record = _make_record()
    parsed = json.loads(formatter.format(record))
    assert "trace_id" not in parsed


def test_single_line_output(formatter):
    record = _make_record("multi\nline\nmessage")
    output = formatter.format(record)
    # json.dumps escapes newlines, so output should be a single line
    assert "\n" not in output
