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
Demo: Transaction Graph Pattern Detection

Builds a synthetic 7-day transaction graph and detects AML patterns:
fan-out, fan-in, cycle, and hub concentration.

All accounts and amounts are randomly generated synthetic data.
Run with: python 02_network_analysis.py
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Transaction:
    tx_id: str
    sender: str
    receiver: str
    amount: float
    day: int


@dataclass
class AccountProfile:
    account_id: str
    out_degree: int = 0
    in_degree: int = 0
    unique_senders: set = field(default_factory=set)
    unique_receivers: set = field(default_factory=set)
    total_sent: float = 0.0
    total_received: float = 0.0


class TransactionGraph:
    """Simplified 7-day sliding transaction graph (illustrative)."""

    FAN_OUT_THRESHOLD = 5
    FAN_IN_THRESHOLD = 5
    HUB_THRESHOLD = 10

    def __init__(self) -> None:
        self.transactions: list[Transaction] = []
        self.profiles: dict[str, AccountProfile] = {}
        self.adjacency: dict[str, list[str]] = defaultdict(list)

    def add(self, tx: Transaction) -> None:
        self.transactions.append(tx)
        for acc_id in (tx.sender, tx.receiver):
            if acc_id not in self.profiles:
                self.profiles[acc_id] = AccountProfile(account_id=acc_id)
        s = self.profiles[tx.sender]
        r = self.profiles[tx.receiver]
        s.out_degree += 1
        s.unique_receivers.add(tx.receiver)
        s.total_sent += tx.amount
        r.in_degree += 1
        r.unique_senders.add(tx.sender)
        r.total_received += tx.amount
        self.adjacency[tx.sender].append(tx.receiver)

    def detect_fan_out(self) -> list[dict]:
        alerts = []
        for acc_id, profile in self.profiles.items():
            if len(profile.unique_receivers) >= self.FAN_OUT_THRESHOLD:
                alerts.append({
                    "pattern": "FAN_OUT",
                    "account": acc_id,
                    "unique_receivers": len(profile.unique_receivers),
                    "total_sent": profile.total_sent,
                    "severity": "HIGH" if len(profile.unique_receivers) >= 10 else "MEDIUM",
                })
        return alerts

    def detect_fan_in(self) -> list[dict]:
        alerts = []
        for acc_id, profile in self.profiles.items():
            if len(profile.unique_senders) >= self.FAN_IN_THRESHOLD:
                alerts.append({
                    "pattern": "FAN_IN",
                    "account": acc_id,
                    "unique_senders": len(profile.unique_senders),
                    "total_received": profile.total_received,
                    "severity": "HIGH" if len(profile.unique_senders) >= 10 else "MEDIUM",
                })
        return alerts

    def detect_cycles(self, max_depth: int = 4) -> list[dict]:
        """Detect simple cycles up to max_depth hops using DFS."""
        alerts = []
        visited_cycles: set[frozenset] = set()

        def dfs(start: str, current: str, path: list[str], depth: int) -> None:
            if depth > max_depth:
                return
            for neighbor in self.adjacency.get(current, []):
                if neighbor == start and len(path) >= 2:
                    cycle_key = frozenset(path)
                    if cycle_key not in visited_cycles:
                        visited_cycles.add(cycle_key)
                        alerts.append({
                            "pattern": "CYCLE",
                            "accounts": path + [start],
                            "hops": len(path),
                            "severity": "HIGH",
                        })
                    return
                if neighbor not in path:
                    dfs(start, neighbor, path + [neighbor], depth + 1)

        for account in list(self.profiles.keys()):
            dfs(account, account, [account], 0)

        return alerts[:10]  # cap at 10 to avoid output flood on dense graphs

    def detect_hubs(self) -> list[dict]:
        alerts = []
        for acc_id, profile in self.profiles.items():
            total_degree = profile.out_degree + profile.in_degree
            if total_degree >= self.HUB_THRESHOLD:
                alerts.append({
                    "pattern": "HUB",
                    "account": acc_id,
                    "total_degree": total_degree,
                    "out_degree": profile.out_degree,
                    "in_degree": profile.in_degree,
                    "severity": "HIGH" if total_degree >= 20 else "MEDIUM",
                })
        return alerts

    def run_detection(self) -> None:
        print(f"\n{'='*60}")
        print("  Transaction Graph — AML Pattern Detection")
        print(f"  {len(self.transactions)} transactions  |  {len(self.profiles)} accounts")
        print(f"{'='*60}")

        all_alerts = (
            self.detect_fan_out()
            + self.detect_fan_in()
            + self.detect_cycles()
            + self.detect_hubs()
        )

        if not all_alerts:
            print("  No AML patterns detected.")
            return

        by_pattern: dict[str, list] = defaultdict(list)
        for a in all_alerts:
            by_pattern[a["pattern"]].append(a)

        for pattern, items in by_pattern.items():
            print(f"\n  [{pattern}] — {len(items)} alert(s)")
            for item in items[:3]:
                if pattern == "FAN_OUT":
                    print(f"    {item['account']}: {item['unique_receivers']} unique receivers, "
                          f"{item['total_sent']:,.0f} TND sent  [{item['severity']}]")
                elif pattern == "FAN_IN":
                    print(f"    {item['account']}: {item['unique_senders']} unique senders, "
                          f"{item['total_received']:,.0f} TND received  [{item['severity']}]")
                elif pattern == "CYCLE":
                    path = " -> ".join(item["accounts"])
                    print(f"    {item['hops']}-hop cycle: {path}  [{item['severity']}]")
                elif pattern == "HUB":
                    print(f"    {item['account']}: degree={item['total_degree']} "
                          f"(out={item['out_degree']}, in={item['in_degree']})  [{item['severity']}]")
            if len(items) > 3:
                print(f"    ... and {len(items) - 3} more")

        high = sum(1 for a in all_alerts if a.get("severity") == "HIGH")
        print(f"\n  Total alerts: {len(all_alerts)}  |  HIGH severity: {high}")
        print(f"{'='*60}\n")


def build_synthetic_graph() -> TransactionGraph:
    """Build a synthetic graph containing all four AML pattern types."""
    g = TransactionGraph()
    txs = []

    # Normal transactions (baseline)
    normal_pairs = [
        ("ACC-A1", "ACC-B1", 1_200), ("ACC-A2", "ACC-B2", 3_500),
        ("ACC-A3", "ACC-B3", 800),   ("ACC-A4", "ACC-B4", 2_100),
        ("ACC-A5", "ACC-B5", 950),   ("ACC-A6", "ACC-B6", 4_200),
    ]
    for i, (s, r, amt) in enumerate(normal_pairs):
        txs.append(Transaction(f"N{i:03d}", s, r, amt, day=1))

    # Fan-out pattern: ACC-LAUNDER sends to 12 accounts (structuring)
    for i in range(12):
        txs.append(Transaction(
            f"FO{i:03d}", "ACC-LAUNDER", f"ACC-DEST{i:02d}", 9_800, day=2
        ))

    # Fan-in pattern: 8 accounts send to ACC-MULE
    for i in range(8):
        txs.append(Transaction(
            f"FI{i:03d}", f"ACC-SRC{i:02d}", "ACC-MULE", 1_500, day=3
        ))

    # Cycle: ACC-X -> ACC-Y -> ACC-Z -> ACC-X
    txs.append(Transaction("CY001", "ACC-X", "ACC-Y", 45_000, day=4))
    txs.append(Transaction("CY002", "ACC-Y", "ACC-Z", 43_000, day=5))
    txs.append(Transaction("CY003", "ACC-Z", "ACC-X", 41_000, day=6))

    # Hub: ACC-HUB has many connections in both directions
    for i in range(6):
        txs.append(Transaction(f"HB_OUT{i}", "ACC-HUB", f"ACC-H{i}", 2_000, day=7))
    for i in range(6, 10):
        txs.append(Transaction(f"HB_IN{i}", f"ACC-H{i}", "ACC-HUB", 1_800, day=7))

    for tx in txs:
        g.add(tx)

    return g


if __name__ == "__main__":
    print("\nAML Fraud Detection Platform — Graph Pattern Detection Demo")
    print("(Synthetic transaction graph — all data is randomly generated)")

    graph = build_synthetic_graph()
    graph.run_detection()
