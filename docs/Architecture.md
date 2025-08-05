# Architecture: AML Fraud Detection Platform

## Overview

The platform is a 6-service streaming system built around Apache Kafka as the
event backbone. Each service has a single responsibility and communicates
exclusively through Kafka topics or REST, with no direct service-to-service calls.

---

## Services

### 1. Transaction API (FastAPI, port 8000)

Entry point for all transactions. Responsibilities:
- JWT authentication (HS256, per-institution API keys)
- Pydantic schema validation (amount, currency, channel, counterparty, country)
- Risk enrichment: attaches account history features before publishing to Kafka
- Publishes to `fraud.transactions` topic

### 2. Kafka Streaming Engine

The core detection service. Consumes `fraud.transactions` and for each event:
1. Routes by transaction type (PAYMENT / DEPOSIT / ATM)
2. Calls XGBoost, HybridGAT, and AML rule engine in parallel
3. Runs context-aware fusion
4. Calls the decision engine
5. Publishes the scored event to `fraud.alerts`
6. Triggers SHAP computation (non-blocking)
7. Triggers LLM audit report for REVIEW/BLOCK events (async)

### 3. Expert Dashboard (Gradio, port 7860)

Compliance officer interface:
- Displays REVIEW-queue transactions with SHAP visualization
- Shows LLM audit report for context
- Collects expert feedback (confirmed fraud / false positive / escalated)
- Publishes feedback events to `fraud.rlhf_feedback`

### 4. MLOps Dashboard (Gradio, port 7861)

Engineering and model operations interface:
- Live F1, AUC, precision, recall per model
- Model weight history (fusion weights, threshold trajectory)
- PSI/KS drift alerts on input feature distributions
- Nightly fine-tuner status (pass/fail/rollback)

### 5. Night Fine-Tuner (scheduled, 22:00 daily)

RLHF recalibration pipeline:
1. Loads expert feedback collected since last run
2. Retrains XGBoost and recalibrates GNN thresholds on augmented dataset
3. Validates: new model must exceed current model F1 on held-out set
4. Deploys if validation passes; auto-rollbacks otherwise
5. Runs morning validator at 08:00 to confirm production health

### 6. Infrastructure (Kafka + Zookeeper + Kafdrop)

- Kafka 7.6.0 on port 9092
- Zookeeper on port 2181
- Kafdrop (optional UI) on port 9000

---

## Kafka Topics

| Topic | Producer | Consumer | Content |
|---|---|---|---|
| `fraud.transactions` | FastAPI | Streaming Engine | Raw transaction events |
| `fraud.alerts` | Streaming Engine | Expert Dashboard, MLOps | Scored alerts with decision |
| `fraud.rlhf_feedback` | Expert Dashboard | Night Fine-Tuner | Expert label events |

---

## Scoring Engine: Component Interaction

```
Transaction Event
      |
      v
 [Feature Adapter]          Normalizes schema across IEEE-CIS, AMLSim, BCT formats
      |
      +-----------> [XGBoost Tabular]     13 engineered features -> score in <5ms
      |
      +-----------> [HybridGAT GNN]       64-d embedding from 7-day sliding graph
      |                                   -> score in <20ms (pre-computed embeddings)
      |
      +-----------> [XGBoost AML]         AML-specific features: velocity, fan-out, cycles
      |             [Rule Engine]         BCT / ACPR / FinCEN hard-threshold rules
      |
      v
 [Context-Aware Fusion]
      |
      ISOLATED (fan_out <= 3):  final = xgb*0.85 + gnn*0.05 + aml*0.30
      DENSE (fan_out > 3):      final = xgb*0.40 + gnn*0.55 + aml*0.30
      |
      v
 [Decision Engine]
      |
      final < 0.20  -> ALLOW
      final < 0.40  -> REVIEW  (+ async SHAP + LLM audit)
      final >= 0.40 -> BLOCK   (+ SHAP + LLM audit)
      rules >= 0.75 -> BLOCK   (hard regulatory override)
```

---

## HybridGAT Architecture

2-layer Graph Attention Network with the following design:

```
Node features (per account, 7-day window):
  - in_degree, out_degree
  - total_sent, total_received
  - unique_counterparties
  - max_single_tx, velocity_24h

Layer 1: GAT (8 attention heads, 64 units per head)
         + BatchNorm + ELU + Dropout(0.3)

Layer 2: GAT (1 attention head, 64 units)
         + BatchNorm

Output:  64-dimensional account embedding
         -> sigmoid -> risk_score in [0, 1]
```

The 7-day sliding graph is maintained in memory with O(1) edge insertion.
New transactions update the graph incrementally; embeddings for active
accounts are recomputed every 60 seconds.

---

## Audit Trail

Every transaction produces an immutable audit record:

```json
{
  "tx_id": "TX-20250815-001",
  "timestamp": "2025-08-15T14:32:01Z",
  "amount": 52400,
  "currency": "TND",
  "channel": "wire",
  "xgb_score": 0.71,
  "gnn_score": 0.83,
  "aml_score": 0.90,
  "rules_triggered": ["BCT_50K_THRESHOLD"],
  "final_score": 0.87,
  "decision": "BLOCK",
  "shap_top_features": [
    {"feature": "amount_tnd", "contribution": 0.31},
    {"feature": "fan_out_degree", "contribution": 0.22}
  ],
  "regulatory_framework": "BCT_CIRCULAR_2021_06",
  "expert_review_status": "PENDING"
}
```

Records are written to SQLite for development and PostgreSQL for production,
with row-level integrity checks and no-delete enforcement for regulatory retention.
