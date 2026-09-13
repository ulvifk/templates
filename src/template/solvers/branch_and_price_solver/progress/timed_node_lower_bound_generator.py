from time import perf_counter

from template.solvers.branch_and_price_solver.bounding.node_lower_bound_generator import (
    NodeLowerBoundGenerator,
)
from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.column_generation.column_generation_result import (
    ColumnGenerationResult,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)
from template.solvers.branch_and_price_solver.progress.node_component import (
    NodeComponent,
)
from template.solvers.branch_and_price_solver.progress.node_observations import (
    NodeObservations,
)


class TimedNodeLowerBoundGenerator(NodeLowerBoundGenerator):
    _inner: NodeLowerBoundGenerator
    _observations: NodeObservations

    def __init__(
        self, inner: NodeLowerBoundGenerator, observations: NodeObservations
    ) -> None:
        self._inner = inner
        self._observations = observations

    def generate(
        self, node: BranchNode, master: MasterProblem, result: ColumnGenerationResult
    ) -> float:
        started_at = perf_counter()
        lower_bound = self._inner.generate(node, master, result)
        self._observations.seconds_by_component[NodeComponent.LOWER_BOUND] = (
            perf_counter() - started_at
        )

        return lower_bound
