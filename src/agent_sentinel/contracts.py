"""Behavioral contract loader and matching primitives."""

from __future__ import annotations

import fnmatch
import ipaddress
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ContractError(ValueError):
    """Raised when an AgentBehaviorContract is malformed."""


@dataclass(frozen=True)
class NetworkRule:
    host: str = ""
    host_suffix: str = ""
    cidr: str = ""
    ports: tuple[int, ...] = ()
    protocols: tuple[str, ...] = ("tcp",)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetworkRule:
        rule = cls(
            host=str(data.get("host") or "").lower(),
            host_suffix=str(data.get("hostSuffix") or "").lower(),
            cidr=str(data.get("cidr") or ""),
            ports=tuple(int(port) for port in data.get("ports", [])),
            protocols=tuple(str(p).lower() for p in data.get("protocols", ["tcp"])),
        )
        if not (rule.host or rule.host_suffix or rule.cidr):
            raise ContractError("network rule requires host, hostSuffix, or cidr")
        if rule.cidr:
            try:
                ipaddress.ip_network(rule.cidr, strict=False)
            except ValueError as exc:
                raise ContractError(f"invalid network CIDR {rule.cidr!r}") from exc
        return rule

    def matches(self, destination: str, port: int | None, protocol: str) -> bool:
        target = destination.lower().rstrip(".")
        identity_match = target == self.host if self.host else False
        if self.host_suffix:
            suffix = self.host_suffix.lstrip(".")
            identity_match = identity_match or target == suffix or target.endswith(f".{suffix}")
        if self.cidr:
            with suppress(ValueError):
                identity_match = identity_match or ipaddress.ip_address(
                    target
                ) in ipaddress.ip_network(self.cidr, strict=False)
        port_match = not self.ports or (port is not None and port in self.ports)
        protocol_match = not protocol or protocol.lower() in self.protocols
        return identity_match and port_match and protocol_match


@dataclass(frozen=True)
class PermissionSet:
    executables: tuple[str, ...] = ()
    files: tuple[str, ...] = ()
    network: tuple[NetworkRule, ...] = ()
    kubernetes_operations: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> PermissionSet:
        data = data or {}
        return cls(
            executables=tuple(str(item) for item in data.get("executables", [])),
            files=tuple(str(item) for item in data.get("files", [])),
            network=tuple(NetworkRule.from_dict(item) for item in data.get("network", [])),
            kubernetes_operations=tuple(str(item) for item in data.get("kubernetesOperations", [])),
        )

    def permits_executable(self, executable: str) -> bool:
        return any(fnmatch.fnmatch(executable, pattern) for pattern in self.executables)

    def permits_file(self, path: str) -> bool:
        return any(fnmatch.fnmatch(path, pattern) for pattern in self.files)

    def permits_network(self, destination: str, port: int | None, protocol: str) -> bool:
        return any(rule.matches(destination, port, protocol) for rule in self.network)

    def permits_kubernetes(self, operation: str) -> bool:
        return any(fnmatch.fnmatch(operation, pattern) for pattern in self.kubernetes_operations)


@dataclass(frozen=True)
class IntentRule:
    intent_id: str
    description: str
    allow: PermissionSet


@dataclass(frozen=True)
class Thresholds:
    restrict: int = 40
    contain: int = 80


@dataclass(frozen=True)
class BehaviorContract:
    """Validated, task-conditioned behavioral contract."""

    name: str
    namespace: str
    pod_pattern: str
    intents: dict[str, IntentRule]
    denied_executables: tuple[str, ...] = ()
    denied_files: tuple[str, ...] = ()
    thresholds: Thresholds = field(default_factory=Thresholds)

    @classmethod
    def from_dict(cls, document: dict[str, Any]) -> BehaviorContract:
        if document.get("apiVersion") != "sentinel.shivam.dev/v1alpha1":
            raise ContractError("apiVersion must be sentinel.shivam.dev/v1alpha1")
        if document.get("kind") != "AgentBehaviorContract":
            raise ContractError("kind must be AgentBehaviorContract")

        metadata = document.get("metadata") or {}
        spec = document.get("spec") or {}
        selector = spec.get("selector") or {}
        hard_deny = spec.get("hardDeny") or {}
        threshold_data = spec.get("thresholds") or {}

        name = str(metadata.get("name") or "")
        namespace = str(selector.get("namespace") or "")
        pod_pattern = str(selector.get("podPattern") or "")
        if not name or not namespace or not pod_pattern:
            raise ContractError(
                "metadata.name, selector.namespace, and selector.podPattern are required"
            )

        intents: dict[str, IntentRule] = {}
        for item in spec.get("intents", []):
            intent_id = str(item.get("id") or "")
            if not intent_id:
                raise ContractError("each intent requires a non-empty id")
            if intent_id in intents:
                raise ContractError(f"duplicate intent id {intent_id!r}")
            intents[intent_id] = IntentRule(
                intent_id=intent_id,
                description=str(item.get("description") or ""),
                allow=PermissionSet.from_dict(item.get("allow")),
            )
        if not intents:
            raise ContractError("at least one intent is required")

        thresholds = Thresholds(
            restrict=int(threshold_data.get("restrict", 40)),
            contain=int(threshold_data.get("contain", 80)),
        )
        if not 0 < thresholds.restrict < thresholds.contain <= 100:
            raise ContractError("thresholds must satisfy 0 < restrict < contain <= 100")

        return cls(
            name=name,
            namespace=namespace,
            pod_pattern=pod_pattern,
            intents=intents,
            denied_executables=tuple(str(item) for item in hard_deny.get("executables", [])),
            denied_files=tuple(str(item) for item in hard_deny.get("files", [])),
            thresholds=thresholds,
        )

    @classmethod
    def load(cls, path: str | Path) -> BehaviorContract:
        try:
            data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise ContractError(f"unable to load contract {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ContractError("contract document must be a YAML mapping")
        return cls.from_dict(data)

    def matches_workload(self, namespace: str, pod: str) -> bool:
        return namespace == self.namespace and fnmatch.fnmatch(pod, self.pod_pattern)

    def is_denied_executable(self, executable: str) -> bool:
        return any(fnmatch.fnmatch(executable, pattern) for pattern in self.denied_executables)

    def is_denied_file(self, path: str) -> bool:
        return any(fnmatch.fnmatch(path, pattern) for pattern in self.denied_files)
