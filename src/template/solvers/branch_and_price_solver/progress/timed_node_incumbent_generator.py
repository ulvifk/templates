from time import perf_counter

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)
from template.solvers.branch_and_price_solver.incumbent.incumbent import Incumbent
from template.solvers.branch_and_price_solver.incumbent.node_incumbent_generator import (
    NodeIncumbentGenerator,
)
from template.solvers.branch_and_price_solver.progress.node_component import (
    NodeComponent,
)
from template.solvers.branch_and_price_solver.progress.node_observations import (
    NodeObservations,
)


class TimedNodeIncumbentGenerator(NodeIncumbentGenerator):
    _inner: NodeIncumbentGenerator
    _observations: NodeObservations

    def __init__(
        self, inner: NodeIncumbentGenerator, observations: NodeObservations
    ) -> None:
        self._inner = inner
        self._observations = observations

    def generate(self, node: BranchNode, master: MasterProblem) -> Incumbent | None:
        started_at = perf_counter()
        incumbent = self._inner.generate(node, master)
        self._observations.seconds_by_component[NodeComponent.INCUMBENT] = (
            perf_counter() - started_at
        )

        return incumbent
