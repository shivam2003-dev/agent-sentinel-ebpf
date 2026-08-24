"""Command line entry point for contract validation and event evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from .adapters import TetragonAdapter
from .contracts import BehaviorContract, ContractError
from .detector import DetectionEngine, ResponseAction
from .responders import KubernetesResponder


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-sentinel",
        description="Evaluate eBPF runtime events against AI-agent behavioral contracts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-contract", help="validate a behavioral contract")
    validate.add_argument("contract", type=Path)

    evaluate = subparsers.add_parser(
        "evaluate", help="evaluate normalized or Tetragon JSONL events"
    )
    evaluate.add_argument("--contract", type=Path, required=True)
    evaluate.add_argument("--events", default="-", help="JSONL file, or - for stdin")
    evaluate.add_argument("--format", choices=("text", "json"), default="text")
    evaluate.add_argument(
        "--response-plan", action="store_true", help="print Kubernetes response plans"
    )
    evaluate.add_argument(
        "--apply-response",
        action="store_true",
        help="apply reversible Pod quarantine labels; requires Kubernetes credentials",
    )
    evaluate.add_argument(
        "--fail-on",
        choices=("never", "restrict", "contain"),
        default="never",
        help="return a non-zero exit status when a decision reaches the selected level",
    )
    return parser


def _stream(path: str) -> tuple[TextIO, bool]:
    if path == "-":
        return sys.stdin, False
    return Path(path).open(encoding="utf-8"), True


def _print_text(decision: object, plan: object | None = None) -> None:
    action = decision.action.value.upper()
    event = decision.event
    detail = decision.findings[0].code if decision.findings else "EXPECTED_BEHAVIOR"
    print(f"{action:<8} risk={decision.risk_score:>3} workload={event.workload_key} {detail}")
    for finding in decision.findings:
        print(f"  - {finding.severity.value:<8} {finding.code}: {finding.reason}")
    if plan is not None:
        for command in plan.printable_commands():
            print(f"  response: {command}")


def _run_evaluate(args: argparse.Namespace) -> int:
    contract = BehaviorContract.load(args.contract)
    engine = DetectionEngine(contract)
    adapter = TetragonAdapter()
    responder = KubernetesResponder()
    threshold_reached = False
    source, should_close = _stream(args.events)
    try:
        for number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
                event = adapter.parse(raw)
            except (json.JSONDecodeError, ValueError) as exc:
                print(f"line {number}: invalid event: {exc}", file=sys.stderr)
                return 2
            if event is None:
                continue
            decision = engine.evaluate(event)
            plan = responder.plan(decision) if args.response_plan or args.apply_response else None
            if args.apply_response and plan is not None and plan.commands:
                responder.apply(plan)
            if args.format == "json":
                output = decision.to_dict()
                if plan is not None:
                    output["response_plan"] = list(plan.printable_commands())
                print(json.dumps(output, sort_keys=True))
            else:
                _print_text(decision, plan)
            if args.fail_on == "restrict" and decision.action in {
                ResponseAction.RESTRICT,
                ResponseAction.CONTAIN,
            }:
                threshold_reached = True
            if args.fail_on == "contain" and decision.action is ResponseAction.CONTAIN:
                threshold_reached = True
    finally:
        if should_close:
            source.close()
    return 3 if threshold_reached else 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate-contract":
            contract = BehaviorContract.load(args.contract)
            print(
                f"valid contract {contract.name!r}: {len(contract.intents)} intent(s), "
                f"selector={contract.namespace}/{contract.pod_pattern}"
            )
            return 0
        return _run_evaluate(args)
    except ContractError as exc:
        print(f"contract error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
