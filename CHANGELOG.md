# Changelog

All notable changes to this showcase repository are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [1.2.0] — 2026-01-20

### Added
- `CONTRIBUTING.md` — contributor guide focused on demo and documentation improvements
- `Makefile` — `make demo`, `make lint`, `make docker-build`
- `.pre-commit-config.yaml` — ruff + pre-commit-hooks
- `.dockerignore` — exclude dev artifacts from Docker build context

### Changed
- Pipeline badge added at top of README
- README Author section includes open-to roles

---

## [1.1.0] — 2025-12-15

### Added
- Unified `pipeline.yml` — replaces separate ci.yml + cd.yml
- `concurrency` group to cancel stale runs
- `docs-check` job: validates internal Markdown links and README structure
- `dependabot.yml` — automated dependency updates

### Changed
- Moved from `workflow_run` trigger to direct `push: branches: [main]`
- Docker publish job now correctly gated on main push + CI success

---

## [1.0.0] — 2025-11-20

### Added
- README: The Problem, The Solution, Architecture, Evaluation Results, Key Capabilities
- `demo/` — self-contained showcase using synthetic transactions
  - `01_single_transaction.py` — single transaction scoring illustration
  - `02_network_analysis.py` — graph pattern detection illustration
- `docs/Architecture.md` — full system design and component diagram
- `docs/EvaluationResults.md` — benchmark results, methodology, honest caveats
- `docs/BusinessCase.md` — ROI framework, compliance value, deployment scenarios
- `docs/UseCases.md` — fraud typologies with detection examples
- `docs/FAQ.md` — common questions
- `ROADMAP.md` — near/medium/long-term enhancements
- `SECURITY.md` — responsible disclosure and private repo notice
- Apache 2.0 license
