# Research Landscape

This review was refreshed on 2026-08-25. It positions the project without claiming that any single
component is new by itself.

## Adjacent bodies of work

### Agent security benchmarks and tool-boundary controls

InjecAgent introduced 1,054 indirect-prompt-injection cases across user and attacker tools, showing
that external content can redirect tool-integrated agents [1]. AgentDojo provides a dynamic test
environment with realistic tasks, security cases, attacks, and defenses [2]. These systems motivate
the compromise scenarios, but primarily evaluate decisions and tool effects at the agent/application
layer.

Recent preprints further emphasize deterministic capability boundaries and provenance. AgentSecBench
formalizes instruction integrity, retrieval confidentiality, and capability integrity [3]. ClawGuard
enforces user-confirmed rules at tool-call boundaries [4], while ARGUS audits whether agent decisions
are justified by trustworthy evidence through an influence-provenance graph [5]. These approaches are
complementary to kernel evidence: a tool gateway can approve an action, while runtime monitoring asks
whether the process produced only the effects implied by that approval.

### Container runtime observability and enforcement

Falco evaluates rules over syscall events enriched with process, user, container, and Kubernetes
context [6]. Tetragon provides Kubernetes-aware eBPF observability and can perform in-kernel filtering
and enforcement for process, file, and network events [7]. Tetragon supports return-value override
and process signals, with documented timing and kernel-support constraints [8].

These tools already solve much of the sensor and enforcement problem. Repackaging their rules for an
AI-agent container would not constitute a sufficient research contribution.

### Kubernetes containment

Kubernetes NetworkPolicy provides L3/L4 controls when implemented by the cluster networking plugin
[9]. Projected service-account tokens are time-limited and Pod-bound; Kubernetes recommends them over
long-lived service-account Secret tokens [10]. These mechanisms supply a response substrate, not an
agent-specific detector.

## Proposed research gap

Agent-layer defenses know which task or tool action was authorized but may not observe hidden child
processes, compromised libraries, or direct system calls. Kernel runtime systems observe these effects
but do not know which high-level agent action justified them.

Agent Sentinel studies this gap through an explicit correlation primitive:

```text
short-lived action authorization + workload identity + process lineage + kernel effects
```

The proposed contribution is not "using eBPF for AI security." It is the design and evaluation of
task-conditioned runtime authorization, including its false-positive/utility trade-off and staged
containment behavior.

## Comparison

| Approach | Knows task intent | Sees kernel effects | Inline system enforcement | Primary role |
|---|:---:|:---:|:---:|---|
| Prompt-only instruction defense | partial | no | no | influence model behavior |
| Tool-input/output firewall | yes | no | at tool boundary | authorize/sanitize tool calls |
| Falco static rules | no | yes | response integration | runtime detection |
| Tetragon tracing policy | no | yes | yes, hook-dependent | runtime visibility/enforcement |
| Kubernetes NetworkPolicy | no | network only | yes, CNI-dependent | workload network segmentation |
| Agent Sentinel hypothesis | yes | yes | staged, substrate-dependent | correlate authorization with effects |

## Claim boundary

The repository demonstrates contract evaluation and response planning. It does not yet establish
superiority over the related systems. That claim requires the experiments in
[research-methodology.md](research-methodology.md). Recent 2026 references are preprints and must be
treated as such until peer review or stronger independent reproduction.

## References

1. Zhan et al., [InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large
   Language Model Agents](https://arxiv.org/abs/2403.02691), 2024.
2. Debenedetti et al., [AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and
   Defenses for LLM Agents](https://arxiv.org/abs/2406.13352), 2024.
3. Alpay and Alpay, [AgentSecBench: Measuring Prompt Injection, Privacy Leakage, and Tool-Use
   Integrity in LLM Agents](https://arxiv.org/abs/2605.26269), 2026 preprint.
4. Zhao et al., [ClawGuard: A Runtime Security Framework for Tool-Augmented LLM Agents Against
   Indirect Prompt Injection](https://arxiv.org/abs/2604.11790), 2026 preprint.
5. Weng et al., [ARGUS: Defending LLM Agents Against Context-Aware Prompt Injection](https://arxiv.org/abs/2605.03378),
   2026 preprint.
6. Falco, [default syscall rules](https://falco.org/docs/reference/rules/default-rules/) and
   [condition syntax](https://falco.org/docs/concepts/rules/conditions/).
7. Tetragon, [overview](https://tetragon.io/docs/overview/) and
   [TracingPolicy](https://tetragon.io/docs/concepts/tracing-policy/).
8. Tetragon, [enforcement model](https://tetragon.io/docs/concepts/enforcement/).
9. Kubernetes, [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/).
10. Kubernetes, [Service Accounts](https://kubernetes.io/docs/concepts/security/service-accounts/).
