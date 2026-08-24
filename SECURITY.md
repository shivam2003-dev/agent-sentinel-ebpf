# Security Policy

Agent Sentinel is experimental research software. It is not a substitute for workload
hardening, least-privilege RBAC, supported NetworkPolicy enforcement, or incident response.

## Supported versions

Security fixes are applied to the latest commit on `main` while the project is pre-1.0.

## Reporting a vulnerability

Do not open a public issue for an undisclosed vulnerability. Use GitHub's private
vulnerability reporting feature for this repository. Include the affected commit, threat
preconditions, reproduction steps, and expected impact. Please do not include real credentials,
production event logs, or personal data.

## Trust boundary

The prototype assumes the Kubernetes node kernel, the eBPF sensor, and the policy controller
remain trusted. A workload with node-root privileges can invalidate those assumptions. See
[the full threat model](docs/threat-model.md) before deploying the prototype.
