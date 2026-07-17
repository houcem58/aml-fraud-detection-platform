# Model Card — AML Fraud Detection Platform

**Version:** 1.0.0  
**Date:** 2025-08-01  
**Author:** Houcem Hammami  
**Framework:** BCT Circular 2021-06 (Tunisia), ACPR (France), FinCEN (USA)  

---

## Model Overview

The AML Fraud Detection Platform uses a multi-model architecture combining three scoring
signals with context-aware fusion to classify financial transactions as ALLOW, REVIEW, or BLOCK.

| Component | Type | Primary signal |
|---|---|---|
| XGBoost Tabular Model | Gradient boosting (13 features) | Amount, channel, country risk, velocity |
| HybridGAT GNN | 2-layer Graph Attention Network (64-d) | Network structure, fan-out, cycles |
| AML Rule Engine | Deterministic threshold rules | BCT/ACPR/FinCEN regulatory thresholds |
| Context-Aware Fusion | Weighted combination | Adapts weights to network density |

---

## Intended Use

**Intended users:** Compliance officers, AML analysts, financial crime operations teams.

**Intended use cases:**
- Real-time transaction screening for money laundering indicators
- Automated filing trigger identification (STR/SAR under BCT Circular 2021-06)
- Priority queue routing for manual compliance review

**Out-of-scope uses:**
- Consumer credit scoring
- Employment, housing, or insurance decisions
- Identity verification
- General-purpose fraud detection outside the financial transaction domain

---

## Architecture Details

### XGBoost Tabular Scorer

| Feature | Type | Description |
|---|---|---|
| `amount_tnd` | Continuous | Transaction amount in Tunisian Dinar |
| `channel_risk` | Categorical → float | Risk weight per channel (ATM: 0.45, wire: 0.35, transfer: 0.20, POS: 0.10) |
| `country_risk` | Categorical → float | Country risk score from FATF/BCT registry |
| `near_threshold` | Binary | 1 if amount within ±10% of BCT reporting threshold |
| `unusual_hour` | Binary | 1 if transaction outside 06:00–22:00 local time |
| `fan_out_degree` | Count | Number of distinct counterparties in recent window |
| `velocity_1h` | Count | Transaction count in preceding 60 minutes |

### HybridGAT GNN

- **Architecture:** 2-layer Graph Attention Network
- **Layer 1:** 8 attention heads, 64 units/head, BatchNorm + ELU + Dropout(0.3)
- **Layer 2:** 1 attention head, 64 units, BatchNorm
- **Output:** 64-dimensional account embedding → sigmoid → score in [0, 1]
- **Graph:** 7-day sliding transaction graph, incremental edge insertion, embedding recomputed every 60 s
- **Node features:** in_degree, out_degree, total_sent, total_received, unique_counterparties, max_single_tx, velocity_24h

### Context-Aware Fusion

```
ISOLATED context (fan_out ≤ 3):
  final = xgb × 0.85 + gnn × 0.05 + aml × 0.30

DENSE-NETWORK context (fan_out > 3):
  final = xgb × 0.40 + gnn × 0.55 + aml × 0.30
```

### Decision Thresholds

| Final score | AML rules score | Decision |
|---|---|---|
| < 0.20 | — | ALLOW |
| 0.20–0.39 | — | REVIEW |
| ≥ 0.40 | — | BLOCK |
| any | ≥ 0.75 | BLOCK (regulatory override) |

---

## Training Data

| Dataset | Description | Source |
|---|---|---|
| IEEE-CIS Fraud Detection | Credit card transaction dataset | Kaggle (public) |
| AMLSim | Synthetic AML transaction simulation | IBM Research (public) |
| BCT synthetic data | Tunisia-specific synthetic transactions | Internal synthetic generation |

**Note:** No personally identifiable information (PII) is used in model training. All account
identifiers are pseudonymized. The model was trained and evaluated on synthetic and publicly
available datasets. Production deployment against real banking data requires additional
validation against the target institution's transaction distribution.

---

## Evaluation Metrics

Evaluated on a held-out synthetic test set (20% split, stratified by label and channel):

| Model | AUC-ROC | F1 (BLOCK) | Precision | Recall | FPR |
|---|---|---|---|---|---|
| XGBoost only | 0.891 | 0.823 | 0.887 | 0.769 | 0.052 |
| GNN only | 0.847 | 0.781 | 0.842 | 0.729 | 0.071 |
| Rule engine only | — | 0.712 | 0.981 | 0.554 | 0.008 |
| **Fusion (full)** | **0.924** | **0.871** | **0.903** | **0.841** | **0.038** |

**Subgroup evaluation:**

| Transaction type | F1 | Notes |
|---|---|---|
| ISOLATED (fan_out ≤ 3) | 0.884 | XGBoost-dominant context |
| DENSE (fan_out > 3) | 0.857 | GNN-dominant context |
| BCT threshold crossings | 0.973 | Hard-rule override ensures near-perfect recall |

---

## Limitations

1. **Synthetic training data:** Performance on real banking transaction distributions may differ.
   Calibration against production data is recommended before deployment.

2. **Graph cold-start:** For accounts with < 7 days of transaction history, GNN embeddings
   are based on sparse graph structure. The system falls back to ISOLATED fusion weights for
   new accounts.

3. **Currency:** The model is calibrated for TND (Tunisian Dinar) thresholds. BCT Circular
   2021-06 amounts (8,000 TND, 30,000 TND, 50,000 TND) are hardcoded. Multi-currency
   deployment requires FX conversion layer.

4. **Regulatory scope:** AML rules are calibrated for BCT (Tunisia), ACPR (France), and
   FinCEN (USA). Other jurisdictions require framework extension.

5. **False positive impact:** REVIEW decisions route transactions to human compliance officers.
   High FPR in the REVIEW band increases analyst workload. Current FPR of 3.8% at BLOCK
   threshold is acceptable for the target deployment scale.

---

## Fairness and Bias Considerations

The model does not use demographic features (age, gender, ethnicity, religion, nationality
as a person attribute). Country risk scores are applied to destination jurisdiction (regulatory
risk), not to account holder nationality.

Channel risk weights are based on transaction channel operational characteristics, not
customer segment. These weights are documented and auditable.

Fairness auditing against protected-class proxies is recommended before production deployment.

---

## Explainability

- **SHAP attribution:** Per-transaction SHAP values computed for XGBoost component (top-10 features)
- **LLM audit reports:** Mistral 7B generates natural-language audit narratives for REVIEW/BLOCK decisions
- **Audit trail:** Every transaction produces an immutable audit record (see [Architecture.md](Architecture.md))
- **Regulatory reference:** Each BLOCK decision references the applicable regulatory framework
  (BCT_CIRCULAR_2021_06, ACPR_ARTICLE_R_561, FINCEN_BSA)

---

## RLHF Recalibration

The `NightFineTunerV2` component runs nightly at 22:00:
1. Loads expert compliance officer feedback (confirmed fraud / false positive / escalated)
2. Retrains XGBoost and recalibrates GNN thresholds on augmented dataset
3. Validation gate: new model must exceed current model F1 on held-out set
4. Auto-rollback if validation fails
5. Morning validator at 08:00 confirms production health

---

## Responsible Use

This model is intended to **assist** compliance officers, not replace human judgment.
All REVIEW decisions require expert human review before any customer-facing action.
BLOCK decisions trigger automated holds but are subject to compliance officer override
within the investigation window defined by applicable regulation.
