# Experimental Methodology

## Objective and preregistration

The experiment asks whether intent-conditioned runtime evidence improves security outcomes over
static runtime controls while retaining legitimate agent utility. Before collecting final results,
publish the contract corpus, attack definitions, primary metrics, exclusion criteria, sample size,
and analysis notebook. Do not tune on the held-out test split.

## Research questions

**RQ1 - Detection.** Does adding action intent to runtime events improve precision and recall for
compromised-agent behavior compared with static runtime rules?

**RQ2 - Containment.** How much does staged inline and Kubernetes containment reduce completed
unauthorized effects, and at what latency?

**RQ3 - Utility.** How often do contracts or containment interrupt benign tasks, including benign
tasks that exhibit previously unseen but legitimate behavior?

**RQ4 - Cost.** What CPU, memory, event-throughput, and end-to-end task-latency overhead is introduced
by sensing, correlation, and response?

## Hypotheses

- **H1:** Hybrid intent plus runtime detection yields higher precision at matched recall than static
  rules because the same operation can be judged in task context.
- **H2:** Inline denial lowers unauthorized-effect completion compared with signal-only or
  post-event Pod quarantine.
- **H3:** Per-task contracts preserve more benign task completion than a global restrictive allowlist.
- **H4:** The correlation engine adds less than 5% median task latency in the controlled lab. This is
  an evaluation target, not a measured result.

## Independent variables

Four detector configurations provide the primary comparison:

1. **Kubernetes baseline:** hardened Pod, least-privilege RBAC, and static NetworkPolicy only.
2. **Static runtime baseline:** curated Falco or Tetragon rules without active intent.
3. **Intent contract only:** tool/action authorization without kernel-effect correlation.
4. **Hybrid:** intent contract, eBPF evidence, risk accumulation, and staged response.

Containment is separately varied across observe-only, signal/process termination, inline denial, and
Pod quarantine. Every run records exact component, kernel, Kubernetes, CNI, model, and image versions.

## Workloads

Use at least three agent roles with materially different legitimate behavior:

- literature agent: reads a corpus and accesses approved scholarly endpoints;
- repository agent: reads/writes a workspace and accesses a source-code service;
- operations agent: reads telemetry and performs a narrow set of Kubernetes read operations.

Each role contains routine tasks, rare-but-valid tasks, and adversarial tasks. Split by task template,
not only by individual run, to reduce leakage between tuning and evaluation.

## Attack matrix

| Attack family | Entry path | Target effect | Runtime evidence |
|---|---|---|---|
| Indirect prompt injection | retrieved page/document | unauthorized command or exfiltration | exec, file, socket |
| Malicious tool output | tool/MCP response | invoke unrelated capability | intent mismatch plus effect |
| Dependency compromise | imported package | hidden child process or connection | lineage, exec, socket |
| Credential abuse | in-Pod code execution | Kubernetes reconnaissance | token read, API audit event |
| Living-off-the-land | allowed interpreter | disallowed file/network action | file/socket outside lease |
| Benign novelty control | new legitimate subtask | authorized uncommon action | expected after explicit lease |

Use reserved documentation IP ranges and controlled cluster services. Do not expose real Secrets or
external attack infrastructure.

## Ground truth

Each scenario has a signed or immutable manifest containing:

- user objective and trusted authorization;
- untrusted input and attack payload identifier;
- permitted and forbidden system effects;
- expected action lease;
- success predicates observable independently from the detector;
- task-utility predicate.

An unauthorized effect is counted only when an independent sink observes it, such as a canary file
read, controlled endpoint request, or audit-recorded forbidden API operation. A detector alert alone
does not prove attack success.

## Metrics

Primary detection metrics:

```text
precision = true positives / (true positives + false positives)
recall    = true positives / (true positives + false negatives)
F1        = 2 * precision * recall / (precision + recall)
```

Primary operational metrics:

- attack success rate and unauthorized-effect completion rate;
- benign task success and approval/interruption rate;
- time from first malicious effect attempt to decision;
- time from decision to verified containment;
- events lost, delayed, or unparseable;
- agent p50/p95 latency, node CPU, memory, and sensor event throughput.

Report confidence intervals, raw counts, and per-attack-family results. A single aggregate score can
hide a defense that works only on obvious shell-spawn attacks.

## Statistical analysis

Use paired scenarios across configurations with randomized execution order. For binary outcomes,
report paired differences and bootstrap confidence intervals; use McNemar's test where assumptions
hold. For latency and resource distributions, report medians, tail percentiles, and non-parametric
paired comparisons. Correct for multiple confirmatory hypotheses or designate a single primary
endpoint before evaluation.

At least two independent random seeds and multiple cluster recreations should be included. Power and
sample-size analysis must be completed after a pilot estimates baseline event rates; the pilot set
must remain outside the final test set.

## Ablation studies

- Remove intent identity but retain the same runtime features.
- Remove process lineage.
- Disable risk accumulation.
- Replace per-task contracts with a global allowlist.
- Compare hostname-derived and IP/CIDR-derived destination identity.
- Compare immediate containment with approval-gated containment.

## Reproducibility artifacts

Publish version-locked manifests, contract files, synthetic data generators, raw anonymized events,
evaluation scripts, environment metadata, and a machine-readable result table. Preserve failed and
excluded runs with reasons. Never publish real tokens, prompts containing private data, or raw
production telemetry.
