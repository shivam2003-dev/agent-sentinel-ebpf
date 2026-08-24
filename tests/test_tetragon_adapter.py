import json
from pathlib import Path

from agent_sentinel.adapters import TetragonAdapter
from agent_sentinel.models import EventType


def fixture(name: str) -> dict[str, object]:
    return json.loads(Path("tests/fixtures", name).read_text(encoding="utf-8"))


def test_parse_process_exec() -> None:
    event = TetragonAdapter().parse(fixture("tetragon-exec.json"))
    assert event is not None
    assert event.event_type is EventType.PROCESS_EXEC
    assert event.namespace == "agent-lab"
    assert event.pod == "research-agent-demo"
    assert event.intent_id == "literature-review"
    assert event.executable == "/bin/bash"


def test_parse_lsm_file_event() -> None:
    event = TetragonAdapter().parse(fixture("tetragon-file.json"))
    assert event is not None
    assert event.event_type is EventType.FILE_ACCESS
    assert event.path == "/var/run/secrets/kubernetes.io/serviceaccount/token"


def test_ignore_unknown_event_family() -> None:
    assert TetragonAdapter().parse({"process_exit": {}}) is None
