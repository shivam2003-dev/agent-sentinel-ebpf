from pathlib import Path

from agent_sentinel.contracts import BehaviorContract
from agent_sentinel.detector import DetectionEngine
from agent_sentinel.models import EventType, RuntimeEvent
from agent_sentinel.responders import KubernetesResponder


def test_containment_plan_is_reversible_label() -> None:
    engine = DetectionEngine(BehaviorContract.load(Path("examples/contracts/research-agent.yaml")))
    decision = engine.evaluate(
        RuntimeEvent(
            event_type=EventType.PROCESS_EXEC,
            namespace="agent-lab",
            pod="research-agent-demo",
            intent_id="literature-review",
            executable="/bin/bash",
        )
    )
    plan = KubernetesResponder().plan(decision)
    assert plan.commands
    assert plan.commands[0][:4] == ("kubectl", "label", "pod", "research-agent-demo")
    assert "sentinel.shivam.dev/state=quarantined" in plan.commands[0]
