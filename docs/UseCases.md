# Use Cases: Supported Fraud Typologies

## 1. Structuring (Smurfing)

**Pattern:** A large sum is broken into multiple smaller transactions, each below
a reporting threshold, to avoid automatic detection and reporting obligations.

**Example:**
```
Original intent: transfer 95,000 TND
Execution:
  ACC-001 → ACC-002: 9,800 TND  (11:02)
  ACC-001 → ACC-003: 9,800 TND  (11:15)
  ACC-001 → ACC-004: 9,800 TND  (11:28)
  ... (10 total, all below 10,000 TND BCT threshold)
```

**Detection:** Fan-out pattern detection in the 7-day sliding graph. ACC-001
shows 10 outbound wires to 10 distinct accounts within 3 hours, all in the
9,500-9,900 TND range. XGBoost AML model trained on structuring features
(amount_near_threshold, velocity_1h, unique_recipient_count_1h) fires.

---

## 2. Layering via Round-Trip

**Pattern:** Funds are moved through a series of accounts to obscure their origin
before eventual extraction.

**Example:**
```
ACC-A → ACC-B: 45,000 EUR  (day 1)
ACC-B → ACC-C: 43,500 EUR  (day 2, minus service fee)
ACC-C → ACC-D: 42,000 EUR  (day 4)
ACC-D → ACC-A: 40,000 EUR  (day 7, minus extraction fee)
```

**Detection:** Cycle detection in the transaction graph identifies the A→B→C→D→A
circular flow. Graph pattern score fires at 0.85. LLM audit: "Detected 4-hop
circular fund movement of 45K EUR with 11% friction losses across 7 days —
consistent with layering to obscure original source. BLOCK + SAR recommended."

---

## 3. Fan-In Collection (Aggregation)

**Pattern:** A recipient account collects small transfers from many senders before
executing a single large outbound transfer — typical of money mule networks.

**Example:**
```
ACC-001 → ACC-TARGET: 800 EUR
ACC-002 → ACC-TARGET: 750 EUR
ACC-003 → ACC-TARGET: 900 EUR
... (38 accounts in 48 hours)
ACC-TARGET → OFFSHORE: 28,500 EUR
```

**Detection:** Fan-in pattern on ACC-TARGET: 38 unique senders in 48 hours,
followed by a single large outbound wire. GNN embedding for ACC-TARGET shifts
from a baseline risk score of 0.12 to 0.91 as the fan-in pattern develops.
Context-aware fusion weights the GNN score heavily (GNN=0.55) due to dense
network activity, producing final_score=0.88 → BLOCK.

---

## 4. High-Risk Jurisdiction Transfer

**Pattern:** Wire transfer to or from a jurisdiction on FATF or ACPR high-risk
country lists, combined with other risk signals.

**Example:**
```
amount: 35,000 EUR
channel: wire
destination_country: XX (FATF grey list)
counterparty: new account (opened 6 days ago)
```

**Detection:** BCT/ACPR rule engine: amount >= 30,000 TND equivalent → rules_score=0.90.
Hard override → BLOCK regardless of ML scores. LLM audit references the specific
FATF grey-list designation and ACPR correspondence banking guideline.

---

## 5. ATM Cash-Out Spike (Mule Liquidation)

**Pattern:** An account that normally has low ATM activity suddenly shows a high
frequency of near-limit ATM withdrawals, consistent with a money mule liquidating
recently received funds.

**Example:**
```
Day 1: received 4,800 EUR wire from flagged account
Day 2: ATM 500 EUR (08:00), 500 EUR (11:30), 500 EUR (14:15), 500 EUR (17:00)
Day 3: ATM 500 EUR (09:00), 500 EUR (12:00)
```

**Detection:** Velocity feature: 6 ATM withdrawals in 30 hours (baseline: 0.3/day).
Incoming wire source has a fraud_history flag from prior SAR. XGBoost score: 0.79.
Decision: REVIEW with SHAP showing atm_velocity_24h and source_fraud_flag as top
contributing features.
