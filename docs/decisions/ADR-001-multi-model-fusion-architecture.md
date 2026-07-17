# ADR-001 — Multi-Model Context-Aware Fusion vs. Single-Model Detection

**Status:** Accepted  
**Date:** 2025-07-01  
**Author:** Houcem Hammami  
**Reviewers:** —  

---

## Context

The AML fraud detection system must classify transactions as ALLOW / REVIEW / BLOCK
in real time (< 50 ms p95) while meeting Tunisia BCT Circular 2021-06 mandatory reporting
thresholds and maintaining regulatory explainability requirements.

The core design question is the model architecture: use a single powerful model, or combine
multiple models with context-aware fusion.

**Option A — Single XGBoost model**  
One tabular model trained on 13 engineered features. Simple, fast, explainable via SHAP.

**Option B — Ensemble (XGBoost + LightGBM) with averaged scores**  
Two tabular models averaged. Reduces variance but both models see the same feature space.

**Option C — Multi-model context-aware fusion (GNN + XGBoost + AML rules)**  
Three independent scoring signals combined with context-dependent weights:
- **XGBoost**: 13 tabular features (amount, channel risk, velocity, country risk)
- **HybridGAT GNN**: 64-d account embedding from 7-day sliding transaction graph
- **AML Rule Engine**: hard regulatory thresholds (BCT, ACPR, FinCEN)

Fusion weights adapt based on transaction network density:
- Isolated transactions (fan_out ≤ 3): `final = xgb×0.85 + gnn×0.05 + aml×0.30`
- Dense-network transactions (fan_out > 3): `final = xgb×0.40 + gnn×0.55 + aml×0.30`

---

## Decision

**Adopted: Option C — Multi-model context-aware fusion.**

---

## Rationale

### The two-signal problem in fraud detection

Fraud patterns split into two structurally different categories:

1. **Transaction-level fraud** — suspicious amount, channel, time, or country. Captured well by
   tabular features. XGBoost excels here.

2. **Network-level fraud** — money mule chains, layering schemes, smurfing. Not visible in
   individual transaction features. Requires graph structure. GNN excels here.

A single XGBoost model cannot learn both simultaneously without feature engineering that
partially encodes graph structure (fan-out degree, velocity) — losing the structural insight
that makes GNNs valuable.

### Why fixed fusion weights fail

A static ensemble (average XGBoost + GNN) would weight both signals equally regardless of
transaction context. This produces:
- Under-weighting of XGBoost for isolated high-risk transactions (e.g., a single large wire
  transfer to a high-risk jurisdiction with no network context)
- Under-weighting of GNN for complex layering schemes where the transaction amount looks normal
  but the graph structure reveals money mule routing

Context-aware fusion solves this by selecting the dominant signal based on the transaction's
structural position in the network.

### Regulatory requirement (BCT Circular 2021-06)

BCT mandates reporting of all transactions exceeding 8,000 TND within 3 days and 50,000 TND
immediately. These are hard regulatory thresholds that cannot be subject to ML confidence.
The AML Rule Engine provides mandatory override capability: regardless of ML scores,
`aml_score ≥ 0.75` → BLOCK, no exceptions.

This requires the rule engine to be a distinct, independently auditable component — not
embedded in the ML model. A single-model architecture cannot enforce this separation.

### Explainability via SHAP + LLM audit reports

BCT and ACPR require transaction-level explanations for BLOCK and REVIEW decisions.
SHAP attribution works naturally on XGBoost but not on the GNN component. The architecture
separates the explanation layer: SHAP explains the XGBoost contribution; the GNN contribution
is explained via the graph structural context (fan-out, cycle detection). LLM audit reports
synthesize both into a compliance-readable narrative.

---

## Consequences

**Positive:**
- Better precision on network-level fraud patterns
- Hard regulatory thresholds enforced via independent rule engine
- Fusion weight logic is auditable and interpretable
- Each model component can be retrained independently

**Negative:**
- GNN requires graph infrastructure (7-day sliding graph in memory)
- End-to-end latency is higher than single-model: XGBoost (~3 ms) + GNN (~18 ms) + fusion
- Model drift monitoring requires separate monitoring per component

**Mitigation:**
- GNN embeddings are pre-computed and cached (recomputed every 60s, not per-transaction)
- The `KafkaStreamingSystem` calls all three scorers in parallel, not sequentially
- The `NightFineTunerV2` retrains each component independently with a validation gate

---

## Alternatives Rejected

| Alternative | Rejection reason |
|---|---|
| Single XGBoost (Option A) | Cannot detect network-level layering; fails on dense-graph smurfing patterns |
| XGBoost + LightGBM average (Option B) | Both models share feature space; no graph structure; no regulatory separation |
| Deep neural network (DNN) end-to-end | Black box; cannot provide per-feature SHAP attribution for BCT compliance |
| Rule-only system | High false negative rate on novel fraud patterns not covered by existing thresholds |

---

## Review Trigger

- If GNN latency exceeds 30 ms p95 under production load
- If the regulatory framework changes to require real-time (< 5 ms) decisions for all channels
- If model drift causes the fusion weight calibration to become invalid (PSI > 0.2 on any input feature)
