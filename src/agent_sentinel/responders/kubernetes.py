"""Kubernetes quarantine responder with safe dry-run behavior."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from ..detector import Decision, ResponseAction


@dataclass(frozen=True)
class ResponsePlan:
    commands: tuple[tuple[str, ...], ...]
    explanation: str

    def printable_commands(self) -> tuple[str, ...]:
        return tuple(" ".join(command) for command in self.commands)


class KubernetesResponder:
    """Generate or execute reversible Pod-quarantine actions."""

    quarantine_label = "sentinel.shivam.dev/state=quarantined"

    def plan(self, decision: Decision) -> ResponsePlan:
        if decision.action is not ResponseAction.CONTAIN:
            return ResponsePlan((), "no Pod quarantine required")
        event = decision.event
        command = (
            "kubectl",
            "label",
            "pod",
            event.pod,
            "--namespace",
            event.namespace,
            self.quarantine_label,
            "--overwrite",
        )
        return ResponsePlan(
            (command,),
            "label the Pod so the pre-installed deny-all NetworkPolicy isolates ingress and egress",
        )

    def apply(self, plan: ResponsePlan) -> None:
        for command in plan.commands:
            subprocess.run(command, check=True, capture_output=True, text=True)
