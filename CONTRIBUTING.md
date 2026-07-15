# Contributing

Thank you for your interest in contributing to the AML Fraud Detection Platform showcase.

> **Note:** This repository contains only the public showcase layer. The full implementation
> (models, training pipeline, Kafka consumers) is in a private repository.
> Contributions here focus on the demo, documentation, and architecture descriptions.

## Ways to Contribute

- **Demo improvements** — extend `demo/examples/` with new fraud pattern illustrations
- **Documentation** — improve any doc in `docs/` (architecture clarity, example additions)
- **Bug reports** — issues in the demo scripts or broken Markdown links
- **Evaluation results** — if you reproduce or extend the benchmark, open an issue to discuss

## Development Setup

```bash
git clone https://github.com/houcem58/aml-fraud-detection-platform.git
cd aml-fraud-detection-platform
pip install pandas numpy
pip install pre-commit
pre-commit install
```

## Running the Demo

```bash
cd demo/examples
python 01_single_transaction.py
python 02_network_analysis.py
```

## Code Standards

- `ruff check demo/` must pass with no errors
- No external dependencies in demo scripts beyond `pandas` and `numpy`
- Demo scripts must be fully self-contained — no API calls, no model files required
- All synthetic data must be clearly labelled as synthetic in comments and output

## Adding a Demo Example

1. Add a new script `demo/examples/03_your_scenario.py`
2. Use only `pandas` and `numpy` (already in requirements)
3. Script must run to completion in under 10 seconds on a laptop
4. Output must be human-readable and clearly show what the scenario illustrates
5. Update `demo/README.md` with a one-line description of the new example

## Documentation Standards

- All docs in `docs/` use standard Markdown
- Internal links must use relative paths (`[Architecture](Architecture.md)`)
- All numeric claims must reference the evaluation methodology in `docs/EvaluationResults.md`
- Honest caveats section is non-negotiable — do not remove or weaken the evaluation caveats

## Pull Request Process

1. Branch from `main` with a descriptive name
2. All CI checks must pass: lint, demo-smoke-test, docs-check
3. Update `CHANGELOG.md` under `[Unreleased]`
4. PRs require one reviewer approval
