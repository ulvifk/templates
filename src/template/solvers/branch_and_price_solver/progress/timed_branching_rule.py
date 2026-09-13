from time import perf_counter

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.branching.branching_rule.branching_rule import (
    BranchingRule,
)
from template.solvers.branch_and_price_solver.progress.node_component import (
    NodeComponent,
)
from template.solvers.branch_and_price_solver.progress.node_observations import (
    NodeObservations,
)


class TimedBranchingRule(BranchingRule):
    _inner: BranchingRule
    _observations: NodeObservations

    def __init__(self, inner: BranchingRule, observations: NodeObservations) -> None:
        self._inner = inner
        self._observations = observations

    def get_children(self, node: BranchNode) -> list[BranchNode]:
        started_at = perf_counter()
        children = self._inner.get_children(node)
        self._observations.seconds_by_component[NodeComponent.BRANCHING] = (
            perf_counter() - started_at
        )

        self._observations.child_count = len(children)

        return children
