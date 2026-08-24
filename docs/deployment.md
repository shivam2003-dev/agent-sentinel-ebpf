# Deployment Guide

## Prerequisites

- Linux Kubernetes nodes with a supported eBPF-capable kernel.
- Tetragon installed and exporting JSON events.
- A CNI that enforces Kubernetes `NetworkPolicy`.
- `kubectl`, Helm, and cluster-admin access for initial lab installation.
- A locally available or published Agent Sentinel image.

macOS can run the CLI and control a Kind cluster, but eBPF executes in Kind's Linux node container.

## 1. Install and verify Tetragon

Follow the maintained Tetragon installation guide rather than pinning an undocumented latest
version. A typical lab installation is:

```bash
helm repo add cilium https://helm.cilium.io
helm repo update
helm install tetragon cilium/tetragon --namespace kube-system
kubectl rollout status -n kube-system daemonset/tetragon
kubectl exec -n kube-system ds/tetragon -c tetragon -- tetra status
```

Confirm JSON export is enabled at `/var/log/tetragon/tetragon.log` and readable by the Agent Sentinel
container. Production deployments should use the Unix-domain gRPC path instead of a shared host log.

## 2. Start in observation mode

```bash
kubectl apply -f policies/tetragon/observe-sensitive-files.yaml
kubectl get tracingpolicy agent-sentinel-sensitive-file-observation
```

Verify BPF LSM before using the LSM hook:

```bash
grep CONFIG_BPF_LSM /boot/config-"$(uname -r)"
cat /sys/kernel/security/lsm
```

The second output must include `bpf`. Managed Kubernetes capabilities vary by node image.

## 3. Build and load the image

```bash
docker build -t ghcr.io/shivam2003-dev/agent-sentinel-ebpf:0.1.0 .

# For Kind:
kind load docker-image ghcr.io/shivam2003-dev/agent-sentinel-ebpf:0.1.0 \
  --name agent-sentinel
```

## 4. Deploy the lab

```bash
kubectl apply -k deploy/kubernetes
kubectl rollout status -n agent-sentinel-system daemonset/agent-sentinel
kubectl rollout status -n agent-lab deployment/research-agent
```

The analyzer service account can only get, list, and patch Pods. The demo agent receives no
service-account token and runs non-root with all Linux capabilities dropped.

## 5. Exercise containment safely

First run replay events locally. In a cluster, inspect analyzer logs and verify the response plan
before enabling `--apply-response` in the DaemonSet.

When a Pod receives the quarantine label:

```bash
kubectl get pod -n agent-lab --show-labels
kubectl describe networkpolicy -n agent-lab agent-sentinel-quarantine
```

Verify isolation with a controlled endpoint. Do not assume a NetworkPolicy object proves packet
enforcement; test the active CNI.

## 6. Opt-in inline file denial

Only after monitor-mode validation:

```bash
kubectl apply -f policies/tetragon/enforce-sensitive-files.yaml
```

The policy uses the `file_open` BPF LSM hook and returns `EACCES` for protected paths in labeled
workloads. Kernel and Tetragon support must be confirmed on every node pool.

## Rollback

```bash
kubectl delete -f policies/tetragon/enforce-sensitive-files.yaml --ignore-not-found
kubectl label pod -n agent-lab POD_NAME sentinel.shivam.dev/state-
kubectl delete -k deploy/kubernetes
kubectl delete -f policies/tetragon/observe-sensitive-files.yaml --ignore-not-found
```

Removing the quarantine label is reversible. Investigate before reconnecting a Pod because the
original compromise may persist in memory or writable volumes.
