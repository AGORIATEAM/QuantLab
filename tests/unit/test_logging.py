import json

import structlog

from quantlab.core.logging import bind_request_context, clear_request_context, configure_logging


def test_logs_are_json_with_correlation_ids(capsys: object) -> None:
    configure_logging("INFO")
    bind_request_context(request_id="req-1", correlation_id="corr-1")
    try:
        structlog.get_logger("test").info("hello", key="value")
    finally:
        clear_request_context()
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    line = json.loads(captured.out.strip().splitlines()[-1])
    assert line["event"] == "hello"
    assert line["request_id"] == "req-1"
    assert line["correlation_id"] == "corr-1"
    assert "timestamp" in line
