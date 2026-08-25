"""Hybrid invariant and intent-deviation detection engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import BehaviorContract, IntentRule
from .models import EventType, RuntimeEvent


class Severity(str, Enum):
    INFO = "info"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResponseAction(str, Enum):
    IGNORE = "ignore"
    ALLOW = "allow"
    RESTRICT = "restrict"
    CONTAIN = "contain"


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    score: int
    reason: str


@dataclass(frozen=True)
class Decision:
    action: ResponseAction
    risk_score: int
    event: RuntimeEvent
    findings: tuple[Finding, ...] = ()
    controls: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "action": self.action.value,
            "risk_score": self.risk_score,
            "workload": self.event.workload_key,
            "event": self.event.to_dict(),
            "findings": [
                {
                    "code": item.code,
                    "severity": item.severity.value,
                    "score": item.score,
                    "reason": item.reason,
                }
                for item in self.findings
            ],
            "controls": list(self.controls),
        }


class DetectionEngine:
    """Evaluate events and maintain a small decaying risk ledger per Pod."""

    def __init__(self, contract: BehaviorContract) -> None:
        self.contract = contract
        self._risk: dict[str, int] = {}

    def evaluate(self, event: RuntimeEvent) -> Decision:
        if not self.contract.matches_workload(event.namespace, event.pod):
            return Decision(ResponseAction.IGNORE, 0, event)

        findings: list[Finding] = self._evaluate_hard_deny(event)
        intent = self.contract.intents.get(event.intent_id)
        if intent is None:
            findings.append(
                Finding(
                    "INTENT_MISSING_OR_UNKNOWN",
                    Severity.HIGH,
                    45,
                    f"event is not bound to a known intent: {event.intent_id or '<missing>'}",
                )
            )
        else:
            findings.extend(self._evaluate_against_intent(event, intent))

        key = event.workload_key
        previous = self._risk.get(key, 0)
        if findings:
            event_risk = max(item.score for item in findings)
            extra = sum(item.score for item in findings if item.score != event_risk) // 4
            current = min(100, int(previous * 0.5) + event_risk + extra)
        else:
            current = max(0, previous - 15)
        self._risk[key] = current

        if current >= self.contract.thresholds.contain:
            action = ResponseAction.CONTAIN
            controls = (
                "deny the triggering operation inline when supported",
                "label the Pod for deny-all network quarantine",
                "terminate the offending process tree",
                "rotate non-Pod-bound credentials after investigation",
            )
        elif current >= self.contract.thresholds.restrict:
            action = ResponseAction.RESTRICT
            controls = (
                "deny or rate-limit the triggering capability",
                "require approval for subsequent high-impact actions",
            )
        else:
            action = ResponseAction.ALLOW
            controls = ()
        return Decision(action, current, event, tuple(findings), controls)

    def _evaluate_hard_deny(self, event: RuntimeEvent) -> list[Finding]:
        """Absolute prohibitions, enforced regardless of intent binding."""

        if event.event_type is EventType.PROCESS_EXEC and self.contract.is_denied_executable(
            event.executable
        ):
            return [
                Finding(
                    "HARD_DENY_EXECUTABLE",
                    Severity.CRITICAL,
                    100,
                    f"executable is explicitly denied: {event.executable}",
                )
            ]
        if event.event_type is EventType.FILE_ACCESS and self.contract.is_denied_file(event.path):
            return [
                Finding(
                    "HARD_DENY_FILE",
                    Severity.CRITICAL,
                    100,
                    f"sensitive path is explicitly denied: {event.path}",
                )
            ]
        return []

    def _evaluate_against_intent(self, event: RuntimeEvent, intent: IntentRule) -> list[Finding]:
        findings: list[Finding] = []
        allow = intent.allow

        if event.event_type is EventType.PROCESS_EXEC:
            if not allow.permits_executable(event.executable):
                findings.append(
                    Finding(
                        "EXECUTABLE_OUTSIDE_INTENT",
                        Severity.HIGH,
                        55,
                        f"intent {intent.intent_id!r} does not allow {event.executable}",
                    )
                )

        elif event.event_type is EventType.FILE_ACCESS:
            if not allow.permits_file(event.path):
                findings.append(
                    Finding(
                        "FILE_OUTSIDE_INTENT",
                        Severity.HIGH,
                        60,
                        f"intent {intent.intent_id!r} does not allow access to {event.path}",
                    )
                )

        elif event.event_type is EventType.NETWORK_CONNECT:
            if not allow.permits_network(event.destination, event.port, event.protocol):
                endpoint = f"{event.destination}:{event.port or '*'}"
                protocol = event.protocol or "network"
                findings.append(
                    Finding(
                        "NETWORK_OUTSIDE_INTENT",
                        Severity.HIGH,
                        65,
                        f"intent {intent.intent_id!r} does not allow {protocol} {endpoint}",
                    )
                )

        elif event.event_type is EventType.KUBERNETES_API and not allow.permits_kubernetes(
            event.kubernetes_operation
        ):
            findings.append(
                Finding(
                    "KUBERNETES_API_OUTSIDE_INTENT",
                    Severity.CRITICAL,
                    85,
                    f"intent {intent.intent_id!r} does not allow {event.kubernetes_operation}",
                )
            )
        return findings
