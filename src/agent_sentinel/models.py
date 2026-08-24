"""Normalized runtime event model used by all sensor adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventType(str, Enum):
    PROCESS_EXEC = "process_exec"
    FILE_ACCESS = "file_access"
    NETWORK_CONNECT = "network_connect"
    KUBERNETES_API = "kubernetes_api"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RuntimeEvent:
    """Sensor-independent representation of a security-relevant action."""

    event_type: EventType
    namespace: str
    pod: str
    timestamp: str = field(default_factory=_utc_now)
    container_id: str = ""
    intent_id: str = ""
    executable: str = ""
    parent_executable: str = ""
    arguments: str = ""
    path: str = ""
    access: str = ""
    destination: str = ""
    port: int | None = None
    protocol: str = ""
    kubernetes_operation: str = ""
    labels: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict, compare=False, repr=False)

    @property
    def workload_key(self) -> str:
        return f"{self.namespace}/{self.pod}"

    @classmethod
    def from_normalized(cls, data: dict[str, Any]) -> RuntimeEvent:
        """Create an event from Agent Sentinel's stable JSONL schema."""

        try:
            event_type = EventType(data["event_type"])
            namespace = str(data["namespace"])
            pod = str(data["pod"])
        except (KeyError, ValueError) as exc:
            raise ValueError(f"invalid normalized runtime event: {exc}") from exc

        port = data.get("port")
        return cls(
            event_type=event_type,
            namespace=namespace,
            pod=pod,
            timestamp=str(data.get("timestamp") or _utc_now()),
            container_id=str(data.get("container_id") or ""),
            intent_id=str(data.get("intent_id") or ""),
            executable=str(data.get("executable") or ""),
            parent_executable=str(data.get("parent_executable") or ""),
            arguments=str(data.get("arguments") or ""),
            path=str(data.get("path") or ""),
            access=str(data.get("access") or ""),
            destination=str(data.get("destination") or ""),
            port=int(port) if port is not None else None,
            protocol=str(data.get("protocol") or "").lower(),
            kubernetes_operation=str(data.get("kubernetes_operation") or ""),
            labels={str(k): str(v) for k, v in (data.get("labels") or {}).items()},
            raw=data,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "namespace": self.namespace,
            "pod": self.pod,
            "container_id": self.container_id,
            "intent_id": self.intent_id,
            "executable": self.executable,
            "parent_executable": self.parent_executable,
            "arguments": self.arguments,
            "path": self.path,
            "access": self.access,
            "destination": self.destination,
            "port": self.port,
            "protocol": self.protocol,
            "kubernetes_operation": self.kubernetes_operation,
            "labels": self.labels,
        }
