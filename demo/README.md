# Demo: AML Fraud Detection Platform

This folder contains self-contained demonstration scripts using **entirely synthetic**
transaction data. No API keys, Kafka, or infrastructure required.

## Quick Start

```bash
pip install pandas numpy
python examples/01_single_transaction.py
python examples/02_network_analysis.py
```

## What the Demo Shows

### 01_single_transaction.py

Simulates the scoring pipeline for a single transaction:
- Tabular feature extraction (amount, channel, country, velocity)
- Deterministic rule engine (BCT threshold check)
- Context-aware fusion of scores
- Decision engine (ALLOW / REVIEW / BLOCK)
- Simulated SHAP top-3 feature attributions

This illustrates the end-to-end decision flow without requiring ML models.

### 02_network_analysis.py

Builds a synthetic 7-day transaction graph and detects AML patterns:
- Fan-out detection: one sender to many recipients
- Fan-in detection: many senders to one recipient
- Cycle detection: circular fund flow
- Hub identification: high-degree accounts

This illustrates the graph topology analysis that feeds the HybridGAT model.

## Sample Data

`sample_data/transactions.csv` contains 200 synthetic transactions:
- 170 normal transactions (random amounts, channels, counterparties)
- 30 structuring-pattern transactions (near-threshold amounts, high fan-out)

All account IDs and amounts are randomly generated and bear no relation to
any real financial institution or customer.
