from pathlib import Path

import pytest

from agent_sentinel.contracts import BehaviorContract, ContractError, NetworkRule

CONTRACT = Path("examples/contracts/research-agent.yaml")


def test_load_contract() -> None:
    contract = BehaviorContract.load(CONTRACT)
    assert contract.name == "research-agent"
    assert set(contract.intents) == {"literature-review", "summarize-local"}
    assert contract.matches_workload("agent-lab", "research-agent-abc")
    assert not contract.matches_workload("default", "research-agent-abc")


def test_network_rule_matches_exact_host_and_port() -> None:
    rule = NetworkRule.from_dict({"host": "api.github.com", "ports": [443]})
    assert rule.matches("api.github.com", 443, "tcp")
    assert not rule.matches("api.github.com", 80, "tcp")
    assert not rule.matches("evil-api.github.com", 443, "tcp")


def test_network_rule_matches_safe_suffix_boundary() -> None:
    rule = NetworkRule.from_dict({"hostSuffix": "arxiv.org", "ports": [443]})
    assert rule.matches("export.arxiv.org", 443, "tcp")
    assert rule.matches("arxiv.org", 443, "tcp")
    assert not rule.matches("notarxiv.org", 443, "tcp")


def test_network_rule_matches_cidr() -> None:
    rule = NetworkRule.from_dict({"cidr": "10.0.0.0/8", "ports": [5432]})
    assert rule.matches("10.2.3.4", 5432, "tcp")
    assert not rule.matches("192.0.2.1", 5432, "tcp")


def test_rejects_invalid_thresholds() -> None:
    document = {
        "apiVersion": "sentinel.shivam.dev/v1alpha1",
        "kind": "AgentBehaviorContract",
        "metadata": {"name": "bad"},
        "spec": {
            "selector": {"namespace": "x", "podPattern": "*"},
            "thresholds": {"restrict": 90, "contain": 80},
            "intents": [{"id": "x"}],
        },
    }
    with pytest.raises(ContractError, match="thresholds"):
        BehaviorContract.from_dict(document)


def test_rejects_duplicate_intents() -> None:
    document = {
        "apiVersion": "sentinel.shivam.dev/v1alpha1",
        "kind": "AgentBehaviorContract",
        "metadata": {"name": "bad"},
        "spec": {
            "selector": {"namespace": "x", "podPattern": "*"},
            "intents": [{"id": "same"}, {"id": "same"}],
        },
    }
    with pytest.raises(ContractError, match="duplicate"):
        BehaviorContract.from_dict(document)
