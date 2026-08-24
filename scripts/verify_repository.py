#!/usr/bin/env python3
"""Repository-level checks that complement unit tests and linters."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CITATION.cff",
    "docs/whitepaper.md",
    "docs/architecture.md",
    "docs/threat-model.md",
    "docs/research-methodology.md",
    "examples/contracts/research-agent.yaml",
    "policies/tetragon/observe-sensitive-files.yaml",
    "deploy/kubernetes/kustomization.yaml",
    "output/pdf/agent-sentinel-whitepaper.pdf",
)


def fail(message: str) -> None:
    raise SystemExit(f"verification failed: {message}")


def verify_files() -> None:
    missing = [name for name in REQUIRED if not (ROOT / name).is_file()]
    if missing:
        fail(f"missing required files: {', '.join(missing)}")


def verify_identity() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix == ".pdf":
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        incorrect_owner = "shive" + "m2003-dev"
        if incorrect_owner in content:
            fail(f"incorrect GitHub owner spelling in {path.relative_to(ROOT)}")


def verify_markdown_links() -> None:
    pattern = re.compile(r"\[[^]]+\]\(([^)]+)\)")
    for path in (ROOT / "README.md", *(ROOT / "docs").glob("*.md")):
        content = path.read_text(encoding="utf-8")
        for target in pattern.findall(content):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            clean = target.split("#", 1)[0]
            if clean and not (path.parent / clean).resolve().exists():
                fail(f"broken local link {target!r} in {path.relative_to(ROOT)}")


def verify_yaml() -> None:
    for directory in ("examples", "deploy", "policies"):
        for path in (ROOT / directory).rglob("*.yaml"):
            try:
                list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
            except yaml.YAMLError as exc:
                fail(f"invalid YAML in {path.relative_to(ROOT)}: {exc}")
    result = subprocess.run(
        ["kubectl", "kustomize", str(ROOT / "deploy/kubernetes")],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        fail(f"kustomize failed: {result.stderr.strip()}")


def verify_pdf() -> None:
    path = ROOT / "output/pdf/agent-sentinel-whitepaper.pdf"
    reader = PdfReader(path)
    if len(reader.pages) < 8:
        fail(f"white paper is unexpectedly short: {len(reader.pages)} pages")
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    for phrase in ("AGENT SENTINEL", "Threat Model", "Experimental Plan", "References"):
        if phrase not in text:
            fail(f"white paper PDF does not contain {phrase!r}")


def main() -> int:
    verify_files()
    verify_identity()
    verify_markdown_links()
    verify_yaml()
    verify_pdf()
    print("repository verification passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
