"""Agent Sentinel: intent-aware runtime security for AI agents."""

from .contracts import BehaviorContract, ContractError
from .detector import Decision, DetectionEngine, Finding
from .models import EventType, RuntimeEvent

__all__ = [
    "BehaviorContract",
    "ContractError",
    "Decision",
    "DetectionEngine",
    "EventType",
    "Finding",
    "RuntimeEvent",
]

__version__ = "0.1.0"
