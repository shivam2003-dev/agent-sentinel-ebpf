from pathlib import Path

from agent_sentinel.contracts import BehaviorContract
from agent_sentinel.detector import DetectionEngine, ResponseAction
from agent_sentinel.models import EventType, RuntimeEvent


def engine() -> DetectionEngine:
    return DetectionEngine(BehaviorContract.load(Path("examples/contracts/research-agent.yaml")))


def event(event_type: EventType, **kwargs: object) -> RuntimeEvent:
    values = {
        "namespace": "agent-lab",
        "pod": "research-agent-test",
        "intent_id": "literature-review",
    }
    values.update(kwargs)
    return RuntimeEvent(event_type=event_type, **values)


def test_expected_execution_is_allowed() -> None:
    decision = engine().evaluate(event(EventType.PROCESS_EXEC, executable="/usr/local/bin/python3"))
    assert decision.action is ResponseAction.ALLOW
    assert decision.risk_score == 0
    assert not decision.findings


def test_unmatched_workload_is_ignored() -> None:
    decision = engine().evaluate(
        RuntimeEvent(
            event_type=EventType.PROCESS_EXEC,
            namespace="default",
            pod="web-1",
            executable="/bin/bash",
        )
    )
    assert decision.action is ResponseAction.IGNORE


def test_unknown_intent_is_restricted() -> None:
    decision = engine().evaluate(
        event(EventType.PROCESS_EXEC, intent_id="unknown", executable="/usr/local/bin/python3")
    )
    assert decision.action is ResponseAction.RESTRICT
    assert decision.findings[0].code == "INTENT_MISSING_OR_UNKNOWN"


def test_hard_denied_shell_causes_containment() -> None:
    decision = engine().evaluate(event(EventType.PROCESS_EXEC, executable="/bin/bash"))
    assert decision.action is ResponseAction.CONTAIN
    assert decision.risk_score == 100
    assert decision.findings[0].code == "HARD_DENY_EXECUTABLE"


def test_secret_access_causes_containment() -> None:
    decision = engine().evaluate(
        event(
            EventType.FILE_ACCESS,
            executable="/usr/local/bin/python3",
            path="/var/run/secrets/kubernetes.io/serviceaccount/token",
        )
    )
    assert decision.action is ResponseAction.CONTAIN
    assert decision.findings[0].code == "HARD_DENY_FILE"


def test_unapproved_network_is_restricted() -> None:
    decision = engine().evaluate(
        event(EventType.NETWORK_CONNECT, destination="203.0.113.5", port=4444, protocol="tcp")
    )
    assert decision.action is ResponseAction.RESTRICT
    assert decision.findings[0].code == "NETWORK_OUTSIDE_INTENT"


def test_approved_network_is_allowed() -> None:
    decision = engine().evaluate(
        event(EventType.NETWORK_CONNECT, destination="export.arxiv.org", port=443, protocol="tcp")
    )
    assert decision.action is ResponseAction.ALLOW


def test_kubernetes_api_violation_causes_containment() -> None:
    decision = engine().evaluate(
        event(EventType.KUBERNETES_API, kubernetes_operation="list:secrets")
    )
    assert decision.action is ResponseAction.CONTAIN
    assert decision.findings[0].code == "KUBERNETES_API_OUTSIDE_INTENT"


def test_hard_deny_applies_even_without_bound_intent() -> None:
    decision = engine().evaluate(
        event(EventType.PROCESS_EXEC, intent_id="unknown", executable="/bin/bash")
    )
    assert decision.action is ResponseAction.CONTAIN
    assert decision.risk_score == 100
    codes = {finding.code for finding in decision.findings}
    assert "HARD_DENY_EXECUTABLE" in codes
    assert "INTENT_MISSING_OR_UNKNOWN" in codes


def test_hard_denied_file_applies_even_without_bound_intent() -> None:
    decision = engine().evaluate(
        event(
            EventType.FILE_ACCESS,
            intent_id="",
            path="/var/run/secrets/kubernetes.io/serviceaccount/token",
        )
    )
    assert decision.action is ResponseAction.CONTAIN
    assert decision.findings[0].code == "HARD_DENY_FILE"


def test_repeated_deviations_accumulate_risk() -> None:
    detector = engine()
    first = detector.evaluate(
        event(EventType.NETWORK_CONNECT, destination="203.0.113.5", port=443, protocol="tcp")
    )
    second = detector.evaluate(
        event(EventType.PROCESS_EXEC, executable="/usr/bin/python-outside-contract")
    )
    assert first.action is ResponseAction.RESTRICT
    assert second.action is ResponseAction.CONTAIN
