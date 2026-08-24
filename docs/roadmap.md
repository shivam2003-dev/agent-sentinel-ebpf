# Roadmap

## v0.1 - executable research MVP

- [x] Behavioral contract schema and validation
- [x] Deterministic hybrid detector and risk ledger
- [x] Tetragon JSON adapter
- [x] Reversible Kubernetes quarantine response
- [x] Synthetic normal and compromised traces
- [x] Tests, CI, Kubernetes manifests, documentation, and white paper

## v0.2 - live experimental platform

- [ ] Tetragon Unix-domain gRPC streaming with offset and health tracking
- [ ] Kubernetes audit-log adapter for `verb:resource` operations
- [ ] Signed, short-lived intent leases bound to Pod UID and process lineage
- [ ] Destination identity enrichment resistant to workload-controlled DNS labels
- [ ] Metrics endpoint for decisions, latency, event loss, and response success
- [ ] Kind-based end-to-end test matrix on supported Linux kernels

## v0.3 - research evaluation

- [ ] Benign task corpus and reproducible attack harness
- [ ] Static-rule, anomaly-only, and hybrid baseline implementations
- [ ] AgentDojo/InjecAgent-inspired runtime scenarios with license review
- [ ] Detection, utility, latency, and resource-overhead measurements
- [ ] Ablations for intent, lineage, risk accumulation, and response level
- [ ] Public anonymized event dataset and experiment manifests

## v1.0 research target

- [ ] Multi-contract controller with admission-time validation
- [ ] Fail-open/fail-closed policy by capability and workload criticality
- [ ] Tetragon enforcement synthesis with per-kernel compatibility checks
- [ ] Credential-rotation integrations with explicit operator approval
- [ ] Independent threat-model review and reproducibility report
