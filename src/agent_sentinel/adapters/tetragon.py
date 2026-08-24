"""Translate Tetragon JSON export events into Agent Sentinel events."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..models import EventType, RuntimeEvent


class TetragonAdapter:
    """Best-effort parser for stable Tetragon process event families."""

    event_keys = ("process_exec", "process_connect", "process_kprobe", "process_lsm")

    def parse(self, raw: dict[str, Any]) -> RuntimeEvent | None:
        if "event_type" in raw:
            return RuntimeEvent.from_normalized(raw)

        event_key = next((key for key in self.event_keys if key in raw), None)
        if event_key is None:
            return None
        payload = raw[event_key]
        if not isinstance(payload, dict):
            return None

        process = payload.get("process") or payload.get("current") or {}
        pod = process.get("pod") or {}
        labels = self._labels(pod.get("labels") or process.get("labels") or {})
        namespace = str(pod.get("namespace") or labels.get("io.kubernetes.pod.namespace") or "")
        pod_name = str(pod.get("name") or labels.get("io.kubernetes.pod.name") or "")
        if not namespace or not pod_name:
            return None

        common = {
            "namespace": namespace,
            "pod": pod_name,
            "timestamp": str(raw.get("time") or raw.get("timestamp") or ""),
            "container_id": str(process.get("docker") or process.get("container_id") or ""),
            "intent_id": labels.get("sentinel.shivam.dev/intent", ""),
            "executable": str(process.get("binary") or ""),
            "parent_executable": str((process.get("parent") or {}).get("binary") or ""),
            "arguments": str(process.get("arguments") or ""),
            "labels": labels,
            "raw": raw,
        }

        if event_key == "process_exec":
            return RuntimeEvent(event_type=EventType.PROCESS_EXEC, **common)

        if event_key == "process_connect":
            destination = payload.get("destination") or {}
            return RuntimeEvent(
                event_type=EventType.NETWORK_CONNECT,
                destination=str(destination.get("ip") or destination.get("address") or ""),
                port=self._integer(destination.get("port")),
                protocol=str(payload.get("protocol") or "tcp").lower(),
                **common,
            )

        function = str(payload.get("function_name") or payload.get("hook") or "")
        if any(token in function for token in ("file", "open", "permission")):
            return RuntimeEvent(
                event_type=EventType.FILE_ACCESS,
                path=self._first_path(payload.get("args") or []),
                access=function,
                **common,
            )
        if any(token in function for token in ("connect", "tcp_sendmsg", "udp_sendmsg")):
            destination, port = self._socket(payload.get("args") or [])
            return RuntimeEvent(
                event_type=EventType.NETWORK_CONNECT,
                destination=destination,
                port=port,
                protocol="udp" if "udp" in function else "tcp",
                **common,
            )
        return None

    @staticmethod
    def _labels(value: Any) -> dict[str, str]:
        if isinstance(value, dict):
            return {str(k): str(v) for k, v in value.items()}
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            labels: dict[str, str] = {}
            for item in value:
                if isinstance(item, str) and "=" in item:
                    key, content = item.split("=", 1)
                    labels[key] = content
            return labels
        return {}

    @classmethod
    def _first_path(cls, value: Any) -> str:
        if isinstance(value, dict):
            if "path" in value:
                return str(value["path"])
            for child in value.values():
                path = cls._first_path(child)
                if path:
                    return path
        elif isinstance(value, list):
            for child in value:
                path = cls._first_path(child)
                if path:
                    return path
        return ""

    @classmethod
    def _socket(cls, value: Any) -> tuple[str, int | None]:
        if isinstance(value, dict):
            for key in ("sock_arg", "socket", "destination"):
                candidate = value.get(key)
                if isinstance(candidate, dict):
                    address = (
                        candidate.get("daddr") or candidate.get("ip") or candidate.get("address")
                    )
                    port = candidate.get("dport") or candidate.get("port")
                    if address:
                        return str(address), cls._integer(port)
            for child in value.values():
                found = cls._socket(child)
                if found[0]:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = cls._socket(child)
                if found[0]:
                    return found
        return "", None

    @staticmethod
    def _integer(value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None
