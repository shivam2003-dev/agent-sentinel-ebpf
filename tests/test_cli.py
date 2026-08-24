import json
from pathlib import Path

import pytest

from agent_sentinel.cli import main

CONTRACT = "examples/contracts/research-agent.yaml"


def test_validate_contract_ok(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate-contract", CONTRACT]) == 0
    assert "valid contract" in capsys.readouterr().out


def test_evaluate_missing_events_file_reports_clean_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        ["evaluate", "--contract", CONTRACT, "--events", "tests/fixtures/does-not-exist.jsonl"]
    )
    assert exit_code == 2
    assert "unable to read events" in capsys.readouterr().err


def test_evaluate_json_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    events = tmp_path / "events.jsonl"
    events.write_text(
        json.dumps(
            {
                "event_type": "process_exec",
                "namespace": "agent-lab",
                "pod": "research-agent-test",
                "intent_id": "literature-review",
                "executable": "/usr/local/bin/python3",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    exit_code = main(
        ["evaluate", "--contract", CONTRACT, "--events", str(events), "--format", "json"]
    )
    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["action"] == "allow"
