from time import perf_counter

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.column_generation.pricing.pricing_problem import (
    PricingProblem,
)
from template.solvers.branch_and_price_solver.column_generation.pricing.pricing_problem_builder import (
    PricingProblemBuilder,
)
from template.solvers.branch_and_price_solver.progress.node_component import (
    NodeComponent,
)
from template.solvers.branch_and_price_solver.progress.node_observations import (
    NodeObservations,
)


class TimedPricingProblemBuilder(PricingProblemBuilder):
    _inner: PricingProblemBuilder
    _observations: NodeObservations

    def __init__(
        self, inner: PricingProblemBuilder, observations: NodeObservations
    ) -> None:
        self._inner = inner
        self._observations = observations

    def build(self, node: BranchNode) -> PricingProblem:
        started_at = perf_counter()
        pricing_problem = self._inner.build(node)
        self._observations.seconds_by_component[NodeComponent.PRICING] = (
            perf_counter() - started_at
        )

        return pricing_problem
