# Copyright 2025–2026 Houcem Hammami
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Demo: Single Transaction Scoring Pipeline

Illustrates the AML scoring flow for one transaction using deterministic
rule-based scoring (no ML models required).

All data is synthetic. Run with: python 01_single_transaction.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from any directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# ── BCT Tunisia regulatory thresholds (TND) ──────────────────────────────────
BCT_THRESHOLDS = {8_000: 0.75, 30_000: 0.90, 50_000: 0.95}

# ── Country risk registry (illustrative subset) ───────────────────────────────
COUNTRY_RISK = {
    "TN": 0.30, "FR": 0.10, "DE": 0.10, "US": 0.15,
    "XX": 0.90,  # FATF grey list placeholder
    "YY": 0.95,  # High-risk jurisdiction placeholder
}

# ── Channel risk weights ──────────────────────────────────────────────────────
CHANNEL_RISK = {"atm": 0.45, "wire": 0.35, "transfer": 0.20, "pos": 0.10}


def extract_features(tx: dict) -> dict:
    """Extract tabular risk features from a raw transaction."""
    amount = tx["amount"]
    channel = tx.get("channel", "transfer").lower()
    country = tx.get("destination_country", "TN")
    hour = tx.get("hour", 12)

    near_threshold = any(
        t * 0.90 <= amount <= t * 1.10 for t in BCT_THRESHOLDS
    )
    unusual_hour = hour < 6 or hour > 22

    return {
        "amount_tnd": amount,
        "channel_risk": CHANNEL_RISK.get(channel, 0.25),
        "country_risk": COUNTRY_RISK.get(country, 0.50),
        "near_threshold": float(near_threshold),
        "unusual_hour": float(unusual_hour),
        "fan_out_degree": tx.get("fan_out_degree", 0),
        "velocity_1h": tx.get("velocity_1h", 1),
    }


def tabular_score(features: dict) -> float:
    """Deterministic tabular risk score (illustrates XGBoost signal logic)."""
    score = 0.0
    amount = features["amount_tnd"]

    # Amount contribution (log-scaled)
    if amount > 0:
        import math
        score += min(0.35, math.log10(amount + 1) / 15)

    score += features["channel_risk"] * 0.25
    score += features["country_risk"] * 0.20
    score += features["near_threshold"] * 0.15
    score += features["unusual_hour"] * 0.05
    score += min(0.20, features["fan_out_degree"] * 0.02)
    score += min(0.10, features["velocity_1h"] * 0.02)

    return min(1.0, score)


def rule_score(tx: dict) -> float:
    """BCT Circular 2021-06 mandatory reporting thresholds."""
    amount = tx["amount"]
    for threshold, score in sorted(BCT_THRESHOLDS.items(), reverse=True):
        if amount >= threshold:
            return score
    return 0.0


def gnn_score_stub(tx: dict) -> float:
    """
    Stub for HybridGAT GNN score (illustrative only).
    In production this is the 64-d account embedding from the sliding graph.
    """
    fan_out = tx.get("fan_out_degree", 0)
    return min(0.95, 0.10 + fan_out * 0.06)


def context_aware_fusion(
    xgb: float, gnn: float, aml: float, fan_out: int
) -> float:
    """
    Blend scores based on network density context:
    - Isolated tx (low fan-out): trust tabular ML more
    - Dense-network tx: shift weight toward GNN
    """
    if fan_out <= 3:
        # ISOLATED context
        xgb_w, gnn_w = 0.85, 0.05
    else:
        # DENSE context
        xgb_w, gnn_w = 0.40, 0.55

    ml_score = xgb * xgb_w + gnn * gnn_w
    final = ml_score * 0.70 + aml * 0.30
    return min(1.0, final)


def decide(final_score: float, rules_score: float) -> str:
    if rules_score >= 0.75:
        return "BLOCK"  # Hard regulatory override
    if final_score >= 0.40:
        return "BLOCK"
    if final_score >= 0.20:
        return "REVIEW"
    return "ALLOW"


def shap_top_features(features: dict, xgb_score: float) -> list[tuple[str, float]]:
    """Illustrative SHAP attributions (deterministic approximation)."""
    contributions = {
        "amount_tnd": min(0.35, xgb_score * 0.40),
        "fan_out_degree": min(0.25, features["fan_out_degree"] * 0.03),
        "country_risk": features["country_risk"] * 0.20,
        "channel_risk": features["channel_risk"] * 0.15,
        "near_threshold": features["near_threshold"] * 0.12,
        "unusual_hour": features["unusual_hour"] * 0.05,
    }
    return sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)[:3]


def score_transaction(tx: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  Transaction: {tx.get('tx_id', 'TX-001')}")
    print(f"{'='*60}")
    print(f"  Amount:      {tx['amount']:,.0f} {tx.get('currency', 'TND')}")
    print(f"  Channel:     {tx.get('channel', 'wire')}")
    print(f"  Country:     {tx.get('destination_country', 'TN')}")
    print(f"  Hour:        {tx.get('hour', 12):02d}:00")
    print(f"  Fan-out:     {tx.get('fan_out_degree', 0)} recent counterparties")
    print()

    features = extract_features(tx)
    xgb = tabular_score(features)
    gnn = gnn_score_stub(tx)
    aml = rule_score(tx)
    fan_out = tx.get("fan_out_degree", 0)
    final = context_aware_fusion(xgb, gnn, aml, fan_out)
    decision = decide(final, aml)

    print(f"  XGBoost score  : {xgb:.3f}")
    print(f"  GNN score      : {gnn:.3f}  (stub)")
    print(f"  AML rules score: {aml:.3f}")
    print(f"  Final score    : {final:.3f}")
    print(f"  Decision       : {decision}")
    print()

    shap = shap_top_features(features, xgb)
    print("  SHAP top features:")
    for feat, val in shap:
        bar = "+" if val >= 0 else "-"
        print(f"    {feat:<20} {bar}{abs(val):.3f}")

    if decision in ("BLOCK", "REVIEW"):
        print()
        print(f"  Audit note: Score {final:.2f} {'(regulatory override)' if aml >= 0.75 else ''}")
        print("  -> Routed to compliance review queue.")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    transactions = [
        {
            "tx_id": "TX-001",
            "amount": 1_200,
            "currency": "TND",
            "channel": "pos",
            "destination_country": "TN",
            "hour": 14,
            "fan_out_degree": 1,
            "velocity_1h": 1,
        },
        {
            "tx_id": "TX-002",
            "amount": 52_400,
            "currency": "TND",
            "channel": "wire",
            "destination_country": "TN",
            "hour": 23,
            "fan_out_degree": 14,
            "velocity_1h": 3,
        },
        {
            "tx_id": "TX-003",
            "amount": 9_800,
            "currency": "TND",
            "channel": "transfer",
            "destination_country": "TN",
            "hour": 11,
            "fan_out_degree": 9,
            "velocity_1h": 8,
        },
    ]

    print("\nAML Fraud Detection Platform — Single Transaction Demo")
    print("(Deterministic scoring illustration — no ML models required)")

    for tx in transactions:
        score_transaction(tx)
