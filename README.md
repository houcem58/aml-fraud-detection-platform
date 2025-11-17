<div align="center">

# AML Fraud Detection Platform — Showcase

### Real-Time Anti-Money Laundering Detection

**Graph Neural Networks · Ensemble ML · Kafka Streaming · SHAP · RLHF**

[![CI](https://github.com/houcem58/aml-fraud-detection-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/houcem58/aml-fraud-detection-platform/actions/workflows/ci.yml)
[![Research](https://img.shields.io/badge/Research-IEEE%20Access-orange)](docs/EvaluationResults.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](docs/Architecture.md)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](demo/examples/)

</div>

---

> A production-oriented AML detection platform combining Graph Neural Networks (HybridGAT),
> ensemble ML (XGBoost + LightGBM), and AML business rules over a Kafka streaming backbone.
> Designed for compliance-driven enterprise environments with full regulatory traceability
> (BCT Tunisia, ACPR France, FinCEN).
>
> **This repository is a portfolio showcase.** The full implementation is private.

---

## The Problem

Financial crime compliance teams operate under two competing pressures: catch every
suspicious transaction before it clears, and avoid false alarms that freeze legitimate
customer activity and generate regulatory friction.

Current approaches fail predictably:

| Approach | Failure Mode |
|----------|-------------|
| Rule-based systems | High recall on known patterns; blind to novel typologies |
| Tabular ML (XGBoost alone) | Ignores network topology — misses layering and structuring |
| Graph analysis alone | Slow, requires graph construction at inference time |
| Manual review | Unscalable at wire-transfer volumes (thousands per minute) |

The core problem is that AML fraud is a **network phenomenon**, not a row-level
phenomenon. Structuring, layering, and fan-in/fan-out patterns are invisible to
models that see transactions in isolation.

---

## The Solution

The platform combines three scoring signals that complement each other:

**Tabular ML captures individual transaction risk.** XGBoost scores each transaction
on amount, channel, country, velocity, and account history features — fast, interpretable,
calibrated on labeled fraud data.

**Graph ML captures network topology risk.** A 2-layer HybridGAT (Graph Attention Network)
embeds each account node using 7-day sliding transaction graphs, producing 64-dimensional
account risk representations that encode structural patterns like fan-in/fan-out, cycling,
and hub concentration.

**AML rule engine captures regulatory thresholds.** Jurisdiction-specific rules (BCT Tunisia
cash reporting thresholds, ACPR high-risk country lists, FinCEN structuring patterns) provide
hard overrides that bypass the ML models when regulatory bright-line rules are triggered.

A context-aware fusion layer blends the three signals: isolated transactions weight tabular
ML heavily (XGB=0.85, GNN=0.05); dense-network transactions shift weight toward the graph
model (XGB=0.40, GNN=0.55).

---

## Architecture

```
Client / Core Banking System
         │
         ▼  POST /transactions (JWT Bearer)
  ┌──────────────────────────┐
  │  FastAPI  :8000          │  JWT auth · Pydantic schema · risk enrichment
  └──────────────────────────┘
         │  Kafka Producer
         ▼
  ┌──────────────────────────┐
  │  Kafka  :9092            │  fraud.transactions · fraud.alerts · fraud.rlhf_feedback
  └──────────────────────────┘
         │  KafkaConsumer
         ▼
  ┌─────────────────────────────────────────────────┐
  │  KafkaStreamingSystem                           │
  │  Routes by tx_type: PAYMENT · DEPOSIT · ATM     │
  │                                                 │
  │  STEP 1 — AI Ensemble Scoring                   │
  │  ┌──────────┐ ┌──────────┐ ┌─────────────────┐ │
  │  │ XGBoost  │ │LightGBM  │ │  HybridGAT GNN  │ │
  │  │ tabular  │ │behavioral│ │  64-d embedding  │ │
  │  └──────────┘ └──────────┘ └─────────────────┘ │
  │        └─────── Context-Aware Fusion ───────────┘
  │                 ISOLATED:  XGB=0.85  GNN=0.05   │
  │                 DENSE:     XGB=0.40  GNN=0.55   │
  │                                                 │
  │  STEP 2 — AML Pattern Detection                 │
  │  XGBoost AML + BCT rules + graph patterns       │
  │  (fan-out / fan-in / cycle / hub)               │
  │                                                 │
  │  STEP 3 — Decision Engine                       │
  │  final < 0.20  →  ALLOW                         │
  │  final < 0.40  →  REVIEW                        │
  │  final >= 0.40 →  BLOCK                         │
  │  rules >= 0.75 →  BLOCK  (hard override)        │
  │                                                 │
  │  STEP 4 — Explainability                        │
  │  SHAP top-10 features (every decision)          │
  │  Mistral 7B audit report (REVIEW / BLOCK)       │
  └─────────────────────────────────────────────────┘
         │
         ├──────────────────────────────────────────┐
         ▼                                          ▼
  ┌──────────────────────────┐     ┌──────────────────────────┐
  │  Expert Dashboard :7860  │     │  MLOps Dashboard  :7861  │
  │  Compliance review       │     │  Model metrics · weights  │
  │  RLHF feedback           │     │  Drift detection (PSI/KS) │
  └──────────────────────────┘     └──────────────────────────┘
         │  Nightly 22:00
         ▼
  ┌──────────────────────────┐
  │  NightFineTunerV2        │  Expert feedback → GNN + XGBoost recalibration
  │  Validation gate         │  Deploy only if new_F1 > current_F1
  │  Auto-rollback           │  Morning validator at 08:00
  └──────────────────────────┘
```

Full design in [docs/Architecture.md](docs/Architecture.md).

---

## Key Capabilities

### Real-Time Graph-Augmented Scoring

Transactions are scored in under 50ms including graph feature extraction. The
7-day sliding transaction graph is maintained in memory and updated incrementally —
no batch graph rebuild at inference time.

```
Input:
  amount=52,400 TND  channel=wire  from=ACC-001  to=ACC-002  country=TN

Output:
  xgb_score:    0.71   (high-amount wire, unusual hour)
  gnn_score:    0.83   (ACC-001 is a fan-out hub, 14 outbound wires in 7 days)
  aml_score:    0.90   (BCT Circular 2021-06: amount >= 50,000 TND)
  final_score:  0.87
  decision:     BLOCK

  SHAP top features:
    amount_tnd (+0.31)  fan_out_degree (+0.22)
    country_risk (+0.18)  hour_of_day (-0.09)

  LLM audit: "Transaction flagged under BCT Circular 2021-06 (large wire).
              ACC-001 shows fan-out pattern: 14 outbound wires to 11 distinct
              recipients in 7 days — consistent with layering. BLOCK recommended
              pending SAR review."
```

### AML Graph Pattern Detection

| Pattern | Description | AML Typology |
|---------|-------------|----------|
| Fan-out | One sender to many recipients in short window | Structuring, layering |
| Fan-in | Many senders to one recipient | Aggregation, collection |
| Cycle | Circular fund flow A to B to C to A | Round-tripping |
| Hub | Account with abnormally high transaction degree | Money mule |

### Expert Feedback Loop (RLHF)

Compliance officers review REVIEW-flagged transactions on the expert dashboard and
mark each as confirmed fraud, false positive, or escalated. Feedback drives nightly
model recalibration with a validation gate: the new model must exceed the current
model's F1 before deployment. Automatic rollback otherwise.

### Regulatory Compliance

| Jurisdiction | Standard | Implementation |
|---|---|---|
| BCT Tunisia | Circular 2021-06 | Reporting thresholds: 8K / 30K / 50K TND |
| ACPR France | AML Directive | Country risk registry, correspondent bank rules |
| FinCEN US | Bank Secrecy Act | Structuring detection, CTR threshold rules |

---

## Evaluation Results

Evaluated on **IBM AMLSim HI-Small** (82,947 transactions, 6.24% fraud rate).
Full methodology in [docs/EvaluationResults.md](docs/EvaluationResults.md).

| Model | Protocol | AUC | F1 |
|---|---|---|---|
| XGBoost + GNN Stacking | P2 warm-start (80/20) | **0.976** | **0.692** |
| HybridGAT + enrichment | P2 warm-start (80/20) | 0.916 | 0.791 |
| Context-Aware Fusion (3-way) | Reproducible rerun | 0.915 | — |
| **XGBoost (strict GroupKFold)** | **P1 5-fold account-disjoint** | **0.925 ± 0.031** | 0.588 ± 0.069 |
| HybridGAT base (strict) | P1 5-fold account-disjoint | 0.689 ± 0.048 | 0.209 ± 0.060 |

> **Honest evaluation:** Under strict account-disjoint GroupKFold (P1), node enrichment
> features collapse to ΔAUC ≈ 0.000 at cold-start. XGBoost + GNN embedding stacking
> is the most reliable route to graph-derived signal under this constraint.

**Decision thresholds:**

| Score Range | Decision | Action |
|---|---|---|
| < 0.20 | LEGIT | ALLOW |
| 0.20 – 0.40 | SUSPECT | REVIEW (expert queue) |
| >= 0.40 | FRAUD | BLOCK |
| rules_score >= 0.75 | Regulatory override | BLOCK |

---

## Technology Stack

| Domain | Technologies |
|---|---|
| Streaming | Apache Kafka, Zookeeper |
| Graph ML | PyTorch Geometric — HybridGAT (2-layer GAT + BatchNorm) |
| Tabular ML | XGBoost, LightGBM |
| API | FastAPI, Pydantic, JWT (HS256) |
| Explainability | SHAP (top-10 per decision), Mistral 7B via Ollama (audit reports) |
| Dashboards | Gradio — Expert review (7860) + MLOps monitoring (7861) |
| Infrastructure | Docker Compose (6 services) |
| Monitoring | PSI/KS drift detection, SQLite audit trail |
| Feedback | RLHF manager, nightly recalibration, validation gate, auto-rollback |

---

## Demo

The [demo/](demo/) folder contains a self-contained illustration of the scoring
pipeline and graph pattern detection using synthetic transaction data. No API keys
or infrastructure required.

```bash
cd demo/examples
pip install pandas numpy
python 01_single_transaction.py
python 02_network_analysis.py
```

See [demo/README.md](demo/README.md) for full instructions.

---

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/Architecture.md) | System design, component interaction, design decisions |
| [Evaluation Results](docs/EvaluationResults.md) | Benchmark methodology, full results, honest caveats |
| [Business Case](docs/BusinessCase.md) | Problem analysis, compliance value, ROI framework |
| [Use Cases](docs/UseCases.md) | Supported fraud typologies with detection examples |
| [FAQ](docs/FAQ.md) | Common questions about the project and research |

---

## Research

Applied AI research conducted at LATICE Laboratory (ENSIT, Université de Tunis).

> Houcem Hammami —
> *Coverage-Aware Evaluation of Account-Risk-Enriched Graph Learning
> for Anti-Money Laundering Detection*
> Published at **IEEE Access**

Key findings:
- Account-risk enrichment is not robust under strict GroupKFold — gain collapses at cold-start
- XGBoost + GNN stacking achieves AUC 0.925 ± 0.031 under account-disjoint cross-validation
- Context-aware fusion outperforms fixed-weight ensembles by 4-7% AUC on dense transaction clusters

---

## About

Built and owned by **Houcem Hammami** — Technical Manager, AI & Data Engineering.

Applied AI research at LATICE Laboratory (ENSIT, Université de Tunis).

**Open to:** Technical Manager — AI & Data Engineering, AI Platform Lead,
Engineering Manager — AI/Data Platforms.

Contact: houcem0508@gmail.com · [GitHub](https://github.com/houcem58)

---

## License

[Apache-2.0](LICENSE) — Code and documentation in this repository.
The full implementation, trained model weights, and evaluation artifacts
remain in a private repository. See [SECURITY.md](SECURITY.md).
