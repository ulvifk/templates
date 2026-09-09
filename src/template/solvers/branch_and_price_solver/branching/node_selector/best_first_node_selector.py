import heapq
import math

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.branching.node_selector.node_selector import (
    NodeSelector,
)


class BestFirstNodeSelector(NodeSelector):
    _heap: list[tuple[float, int, BranchNode]]  # (lower bound, insertion order, node)
    _insertion_count: int

    def __init__(self) -> None:
        self._heap = []
        self._insertion_count = 0

    def push(self, nodes: list[BranchNode]) -> None:
        for node in nodes:
            heapq.heappush(self._heap, (node.lower_bound, self._insertion_count, node))
            self._insertion_count += 1

    def pop(self) -> BranchNode | None:
        if not self._heap:
            return None

        return heapq.heappop(self._heap)[2]

    def get_best_lower_bound(self) -> float:
        if not self._heap:
            return math.inf

        return self._heap[0][0]
