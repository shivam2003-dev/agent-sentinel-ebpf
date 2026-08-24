.PHONY: install lint test demo-normal demo-attack whitepaper verify

install:
	python3 -m pip install -e '.[dev,pdf]'

lint:
	ruff check src tests scripts

test:
	pytest

demo-normal:
	agent-sentinel evaluate --contract examples/contracts/research-agent.yaml --events examples/events/normal.jsonl --response-plan

demo-attack:
	agent-sentinel evaluate --contract examples/contracts/research-agent.yaml --events examples/events/compromised.jsonl --response-plan

whitepaper:
	python3 scripts/build_whitepaper.py

verify: lint test whitepaper
	python3 scripts/verify_repository.py
