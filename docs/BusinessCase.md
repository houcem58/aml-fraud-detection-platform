# Business Case: AML Fraud Detection Platform

## The Compliance Burden

Financial institutions in the EU, US, and MENA region face mandatory AML
transaction monitoring under:

- **FATF Recommendations** — 40 standards requiring transaction monitoring,
  customer due diligence, and suspicious activity reporting
- **EU 6AMLD (Sixth Anti-Money Laundering Directive)** — Criminal liability for
  senior executives on compliance failures
- **BCT Circular 2021-06 (Tunisia)** — Mandatory cash equivalent reporting for
  wire transfers above 8,000 TND
- **FinCEN SAR regulations** — Mandatory Suspicious Activity Reports within 30
  days of detection for US-regulated institutions

The cost of non-compliance is existential: BNP Paribas paid $8.9B (2014),
Goldman Sachs $2.9B (2020), and Westpac $1.3B (2020) in AML-related fines.

## Why Existing Systems Fail

### Rule-Based Systems

Legacy AML platforms (Actimize, Mantas) rely on manually authored rule sets.
Rules catch known patterns but generate false positive rates of 95-98% — meaning
compliance teams spend 95% of their review time on legitimate transactions.

At a mid-sized bank processing 100,000 transactions per day with a 2% alert rate:
- 2,000 alerts generated per day
- 1,900 are false positives
- Each takes 15-30 minutes to review
- Cost: 475-950 analyst-hours per day

### Tabular ML Without Graph Context

Gradient boosting models trained on transaction features reduce false positives
by 30-50% over rule systems but remain blind to network topology. A structuring
scheme that splits a 100K wire into 10 × 9,999 transfers across different accounts
looks like 10 legitimate small transactions in isolation — but is immediately
visible as a fan-out pattern in the transaction graph.

## Value Proposition

### False Positive Reduction

By combining tabular ML with GNN-derived graph features, the platform identifies
network-topology signals that suppress false positives without reducing recall:

- Context-aware fusion suppresses tabular false alarms for accounts with clean
  network profiles (low fan-out, no cycle involvement, stable counterparties)
- The GNN's 64-dimensional account embedding encodes structural risk that tabular
  features cannot represent

Estimated impact on a 100K tx/day institution: 40-60% reduction in analyst review
load while maintaining recall on high-confidence fraud.

### Audit-Ready Explainability

Every decision is traceable:
- SHAP top-10 features quantify each model's contribution to the score
- LLM audit reports (Mistral 7B) verbalize SHAP signals and AML pattern evidence
  in human-readable format for compliance officer review
- Immutable audit trail per transaction for regulatory examination

This directly addresses the EU's requirements for explainable automated decisions
under GDPR Article 22 and the EBA Guidelines on Internal Governance.

### Continuous Adaptation via RLHF

AML typologies evolve as fraudsters adapt. The nightly recalibration loop
incorporates expert feedback continuously, allowing the model to adapt to new
patterns within days rather than waiting for annual model updates. The validation
gate ensures model degradation cannot be deployed silently.

## ROI Framework

| Metric | Baseline (Rules Only) | With Platform | Delta |
|---|---|---|---|
| False positive rate | 95-98% | 50-65% (estimate) | -30-45pp |
| Analyst review hours/day | 475-950 | 250-500 (estimate) | -50% |
| Time to detect new typology | Weeks (rule authoring) | Days (RLHF loop) | -80% |
| Explainability for regulator | Manual narrative | Auto-generated audit | Automated |
| SAR draft preparation | 1-2 hours per SAR | LLM draft + review | -70% |
