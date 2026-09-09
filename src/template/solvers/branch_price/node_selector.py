import heapq
import itertools
import math
from collections.abc import Iterator

from template.solvers.branch_price.branch_node import BranchNode


class NodeSelector:
    """Best first over the open nodes; the insertion counter keeps nodes from ever being compared."""

    _open_nodes: list[tuple[float, int, BranchNode]]
    _counter: Iterator[int]

    def __init__(self) -> None:
        self._open_nodes = []
        self._counter = itertools.count()

    def push(self, nodes: list[BranchNode]) -> None:
        for node in nodes:
            heapq.heappush(
                self._open_nodes, (node.lower_bound, next(self._counter), node)
            )

    def pop(self) -> BranchNode | None:
        if not self._open_nodes:
            return None
        _, _, node = heapq.heappop(self._open_nodes)
        return node

    def get_open_bound(self) -> float:
        """The weakest bound the open tree still has to beat; infinite once the tree is exhausted."""
        if not self._open_nodes:
            return math.inf
        return min(bound for bound, _, _ in self._open_nodes)

    def is_empty(self) -> bool:
        return not self._open_nodes
