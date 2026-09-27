"""
Cross-district redistribution recommender.

For a given medicine, compute each PHC's surplus (stock above what its own
forecast says it needs over the procurement lead time) or deficit (stock
below that need). Greedily match the largest surplus PHCs to the largest
deficit PHCs so that no PHC's redistribution ever pushes it below its own
safety threshold. This is a transportation-problem heuristic (not full
linear-programming optimality) chosen because it needs to explain itself
in one sentence to a district health officer approving the transfer.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class PHCPosition:
    phc_id: int
    phc_name: str
    district_name: str
    current_qty: float
    required_qty: float  # forecast demand over lead time + safety buffer

    @property
    def net(self) -> float:
        return self.current_qty - self.required_qty


@dataclass
class RedistributionMove:
    from_phc_id: int
    to_phc_id: int
    qty: float


def recommend_redistribution(positions: List[PHCPosition]) -> List[RedistributionMove]:
    surplus = sorted([p for p in positions if p.net > 0], key=lambda p: -p.net)
    deficit = sorted([p for p in positions if p.net < 0], key=lambda p: p.net)  # most negative first

    surplus_pool = [[p.phc_id, p.net] for p in surplus]
    moves: List[RedistributionMove] = []

    for d in deficit:
        need = -d.net
        for s in surplus_pool:
            if need <= 0:
                break
            if s[1] <= 0:
                continue
            take = min(s[1], need)
            if take <= 0:
                continue
            moves.append(RedistributionMove(from_phc_id=s[0], to_phc_id=d.phc_id, qty=round(take, 1)))
            s[1] -= take
            need -= take

    return moves
