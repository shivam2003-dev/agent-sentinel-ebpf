# Contributing

Contributions are welcome, especially reproducible attack traces, sensor adapters, contract
semantics, and evaluation methodology improvements.

1. Open an issue describing the proposed behavior and its security assumptions.
2. Create a focused branch and add tests for behavioral changes.
3. Run `make verify` before opening a pull request.
4. Keep enforcement disabled by default in examples unless the safety trade-off is explicit.

Never commit credentials, production Tetragon logs, model prompts containing private data, or
unlicensed benchmark content. Research results must distinguish measured evidence from proposed
hypotheses.
