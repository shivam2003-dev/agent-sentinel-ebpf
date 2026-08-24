# Changelog

All notable changes to Agent Sentinel are documented here. The project follows semantic versioning
after the initial research-prototype phase.

## 0.1.0 - 2026-08-25

### Added

- Intent-conditioned `AgentBehaviorContract` schema and validator.
- Explainable process, file, network, and Kubernetes API deviation detector.
- Decaying per-Pod risk ledger with allow, restrict, and contain decisions.
- Normalized JSONL and Tetragon event adapters.
- Reversible Kubernetes quarantine response and deny-all NetworkPolicy.
- Hardened demo workload, patch-only response RBAC, and monitor-first Tetragon policies.
- Synthetic benign and compromised event replays with 19 automated tests.
- Architecture, threat model, research landscape, experimental methodology, deployment guide,
  roadmap, and an eight-page rendered white paper.
