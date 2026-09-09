import math

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.branching.node_selector.node_selector import (
    NodeSelector,
)


class DepthFirstNodeSelector(NodeSelector):
    _stack: list[BranchNode]

    def __init__(self) -> None:
        self._stack = []

    def push(self, nodes: list[BranchNode]) -> None:
        self._stack.extend(reversed(nodes))  # so the first child is popped first

    def pop(self) -> BranchNode | None:
        if not self._stack:
            return None

        return self._stack.pop()

    def get_best_lower_bound(self) -> float:
        if not self._stack:
            return math.inf

        return min(node.lower_bound for node in self._stack)
