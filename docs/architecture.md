# Architecture

## Design objective

Agent Sentinel tests whether an agent's authorized high-level action can be reconciled with the
kernel-visible effects produced by its container. The design intentionally separates four layers:

1. **Intent plane** - a behavioral contract states which capabilities are valid for a task phase.
2. **Execution plane** - an agent and its tools execute inside a Kubernetes Pod.
3. **Evidence plane** - Tetragon emits process, file, and network events enriched with workload
   identity.
4. **Response plane** - Agent Sentinel scores deviations and activates a bounded containment action.

This separation makes the prototype model-agnostic. The detector evaluates effects, not chain of
thought, prompt wording, or a model-provider-specific API.

## Data flow

```text
Agent action / Pod intent label
             │
             ▼
AgentBehaviorContract ─────────┐
                               ▼
Tetragon JSON event ──► adapter ──► normalized RuntimeEvent
                                        │
                                        ▼
                             invariant + intent checks
                                        │
                             decaying per-Pod risk ledger
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
                  allow              restrict             contain
                                         │                   │
                                         └──────► quarantine label
                                                         │
                                                         ▼
                                             deny-all NetworkPolicy
```

## Behavioral contract semantics

An `AgentBehaviorContract` selects a namespace and Pod-name pattern. Each intent defines positive
permissions for:

- executable paths;
- file path globs;
- destination hostnames, suffixes, CIDRs, ports, and protocols;
- Kubernetes operations represented as `verb:resource` strings.

Hard-deny executable and file patterns override intent permissions. Unknown intent identifiers are
deviations. The prototype intentionally requires positive network authorization; an empty list means
no network destination is allowed for that intent.

The active intent currently comes from `sentinel.shivam.dev/intent`. This label is convenient for a
reproducible MVP but is not strong authorization. The planned design replaces it with a signed,
short-lived action lease containing the Pod UID, process identity, capability set, nonce, issuer,
and expiry.

## Detection and response

Each finding contributes a severity-calibrated score. The risk ledger retains half of the previous
score when a new deviation arrives and subtracts 15 after expected behavior. The mechanism is
transparent and deterministic so experiments can explain every decision. It is not presented as a
learned anomaly model.

Default thresholds:

| Score | Decision | Meaning |
|---:|---|---|
| 0-39 | allow | observed behavior is expected or below the restriction threshold |
| 40-79 | restrict | capability should be denied, rate-limited, or approval-gated |
| 80-100 | contain | isolate the Pod and terminate the offending process through an enforcement layer |

The bundled responder only applies the reversible quarantine label. The pre-installed
`NetworkPolicy` selects that label and declares empty ingress and egress rule sets. Actual packet
enforcement depends on the cluster's network plugin.

## Sensor integration

The adapter accepts Agent Sentinel's normalized JSONL and these Tetragon families:

- `process_exec` for binary and process ancestry;
- `process_connect` for destination and port;
- `process_lsm` for file-open hooks;
- relevant `process_kprobe` events for file and socket operations.

Tetragon's default export file is suitable for the lab. A production implementation should consume
the protected Unix-domain gRPC endpoint, authenticate the sensor, persist event offsets, and handle
backpressure and sensor health explicitly.

## Prototype boundaries

- The MVP correlates one active intent per Pod; it does not issue cryptographically protected leases.
- Hostname permissions require trusted destination enrichment. Raw eBPF socket events commonly carry
  IP addresses, so production enforcement must resolve policies without trusting workload-provided
  DNS claims.
- Kubernetes API events use the normalized schema; Kubernetes audit-log ingestion is planned.
- The detector is rule-based. The proposed anomaly component and learning evaluation are future work.
- Tetragon policies and kernel capabilities vary. BPF LSM and override support must be checked on the
  target nodes.
- NetworkPolicy is L3/L4 and CNI-dependent. It cannot revoke data already read or terminate an
  already-completed operation.
- A node-root or kernel compromise is outside the current trust boundary.
