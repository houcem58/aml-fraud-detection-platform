# Platform Roadmap

## Current State (Production Ready)

The platform implements the core detection pipeline end-to-end:
real-time Kafka streaming, HybridGAT GNN scoring, XGBoost ensemble,
AML pattern detection, SHAP explainability, RLHF feedback loop, and
regulatory compliance framework (BCT / ACPR / FinCEN).

Evaluated on IBM AMLSim HI-Small with AUC 0.925 ± 0.031 under strict
account-disjoint GroupKFold — the honest production-relevant evaluation protocol.

---

## Roadmap

### Near-Term (Production Hardening)

- **Cold-start enrichment:** Graph embedding precomputation for new accounts
  using population-level priors, eliminating the GroupKFold collapse at
  account boundaries
- **Temporal graph evolution:** Replace 7-day sliding window with full
  account history graph using temporal GNN (TGN / DyRep)
- **Multi-relational graph:** Add beneficial ownership and correspondent
  banking edges to the transaction graph — improves hub and cycle detection
- **Sub-50ms latency guarantee:** Profile and optimize the GNN embedding
  path; add model quantization (INT8) for inference

### Medium-Term (Enterprise Integration)

- **Core banking connectors:** Native adapters for SWIFT MT103, ISO 20022,
  and SEPA Credit Transfer message formats
- **SAR auto-draft:** LLM-generated Suspicious Activity Report drafts from
  SHAP signals + graph evidence, formatted for FinCEN/ACPR submission
- **Federated detection:** Privacy-preserving model training across multiple
  financial institution data silos using federated learning
- **Real-time dashboard:** Grafana-based operations dashboard with alert
  routing to compliance queues

### Longer-Term (Research Extensions)

- **Benchmark contribution:** Open-source the AMLSim evaluation harness and
  GroupKFold protocol as a reproducible benchmark for AML detection research
- **Heterogeneous graph:** Incorporate entity types beyond accounts and
  transactions — companies, beneficial owners, jurisdictions — as graph nodes
- **Counterfactual explanations:** Generate minimal-change counterfactuals
  ("This transaction would have been ALLOWED if the amount were below 45K TND")
  for compliance officer review
