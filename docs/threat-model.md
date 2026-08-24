# Threat Model

## Assets

- Kubernetes Secrets, projected service-account tokens, workload identity, and cloud credentials.
- Source code, user documents, retrieved private data, and tool outputs available to an agent.
- Integrity of actions performed through browsers, shells, APIs, databases, and cluster tools.
- Availability of the agent workload and surrounding tenant workloads.
- Integrity and confidentiality of runtime evidence and behavioral contracts.

## Adversaries and entry paths

The primary adversary can influence an agent without initially controlling the node:

- indirect prompt injection in web pages, documents, tickets, logs, or tool output;
- malicious or compromised MCP/tool server;
- dependency or container-image compromise;
- leaked agent credential or service-account token;
- model or orchestration error that produces unsafe tool use;
- an attacker with code execution inside the agent container.

## Covered behaviors

| Technique | Observable evidence | MVP decision |
|---|---|---|
| Spawn an unapproved shell or utility | process execution and lineage | restrict or contain |
| Read a mounted Secret/token path | LSM file-open event | contain when hard-denied |
| Connect to an unapproved endpoint | socket destination and port | restrict; repeated deviations contain |
| Call an unauthorized Kubernetes API | normalized audit operation | contain |
| Hide activity in a child process | child executable plus Pod identity | evaluate against the same intent |

## Trust assumptions

The node kernel, Tetragon agent, contract issuer, Agent Sentinel controller, Kubernetes API server,
and the CNI enforcement path are trusted. Contracts and response configuration are available only to
authorized administrators. Time and workload identity supplied by the control plane are sufficiently
accurate for correlation.

The AI model, agent process, child processes, tools, retrieved content, third-party services, and
network destinations are untrusted.

## Explicitly out of scope for v0.1

- Kernel, hypervisor, kubelet, CNI, or Tetragon compromise.
- Hardware side channels and physical attacks.
- Detection based solely on encrypted application payload content.
- Recovery of a Secret after successful read or exfiltration.
- Proving that a semantically harmful action is malicious when its system effects are fully allowed.
- Cross-cluster identity revocation and cloud-provider credential rotation.
- Fully autonomous destructive remediation.

## Security failure modes

**False negative:** an attack uses only allowed capabilities. Mitigation requires narrower contracts,
short-lived leases, provenance at the tool boundary, and application-layer validation.

**False positive:** a legitimate task introduces a new binary or endpoint. Mitigation requires
monitor-first rollout, task-specific contracts, explanation, and approval-gated restriction.

**Race:** a kill signal follows an operation that already completed. High-confidence prevention
should use inline return-value override or a dedicated authorization proxy where supported.

**Sensor evasion or outage:** missing events appear as silence. Production design must measure sensor
health and choose a fail-open or fail-closed mode per capability.

**Policy tampering:** a privileged attacker changes contracts or Tetragon policy. Use narrow RBAC,
admission control, signed policy artifacts, and audit logging.

## Safe response policy

The repository defaults to observation and response-plan output. `--apply-response` only adds a
reversible label. Automatic Pod deletion, credential revocation, and process killing are excluded
from the controller MVP. The opt-in Tetragon enforcement policy is isolated in a clearly named file
and must be validated in a disposable cluster.
