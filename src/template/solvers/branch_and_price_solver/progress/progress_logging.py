from dataclasses import replace
from time import perf_counter

from template.model.solve_result import SolveResult
from template.solvers.branch_and_price_solver.branch_and_price_config import (
    BranchAndPriceConfig,
)
from template.solvers.branch_and_price_solver.branch_and_price_observer import (
    BranchAndPriceObserver,
)
from template.solvers.branch_and_price_solver.explored_node import ExploredNode
from template.solvers.branch_and_price_solver.progress.node_observations import (
    NodeObservations,
)
from template.solvers.branch_and_price_solver.progress.node_record import NodeRecord
from template.solvers.branch_and_price_solver.progress.progress_logger import (
    ProgressLogger,
)
from template.solvers.branch_and_price_solver.progress.timed_branching_rule import (
    TimedBranchingRule,
)
from template.solvers.branch_and_price_solver.progress.timed_column_generation import (
    TimedColumnGeneration,
)
from template.solvers.branch_and_price_solver.progress.timed_master_problem_builder import (
    TimedMasterProblemBuilder,
)
from template.solvers.branch_and_price_solver.progress.timed_node_incumbent_generator import (
    TimedNodeIncumbentGenerator,
)
from template.solvers.branch_and_price_solver.progress.timed_node_lower_bound_generator import (
    TimedNodeLowerBoundGenerator,
)
from template.solvers.branch_and_price_solver.progress.timed_pricing_problem_builder import (
    TimedPricingProblemBuilder,
)


class ProgressLogging(BranchAndPriceObserver):
    """Wraps the config's components to time them and logs one row per explored node."""

    _observations: NodeObservations
    _logger: ProgressLogger

    _started_at: float
    _node_count: int

    def __init__(self) -> None:
        self._observations = NodeObservations()
        self._logger = ProgressLogger()

        self._node_count = 0

    def wrap(self, config: BranchAndPriceConfig) -> BranchAndPriceConfig:
        return replace(
            config,
            branching_rule=TimedBranchingRule(
                config.branching_rule, self._observations
            ),
            master_problem_builder=TimedMasterProblemBuilder(
                config.master_problem_builder, self._observations
            ),
            pricing_problem_builder=TimedPricingProblemBuilder(
                config.pricing_problem_builder, self._observations
            ),
            column_generation=TimedColumnGeneration(
                config.column_generation, self._observations
            ),
            node_lower_bound_generator=TimedNodeLowerBoundGenerator(
                config.node_lower_bound_generator, self._observations
            ),
            node_incumbent_generator=TimedNodeIncumbentGenerator(
                config.node_incumbent_generator, self._observations
            ),
            observers=[*config.observers, self],
        )

    def on_search_started(self, started_at: float) -> None:
        self._started_at = started_at
        self._node_count = 0
        self._observations.clear()
        self._logger.reset()

    def on_node_explored(self, explored: ExploredNode) -> None:
        self._node_count += 1

        record = self._build_node_record(explored)
        self._logger.log_node(record)

        self._observations.clear()

    def on_search_finished(self, result: SolveResult) -> None:
        self._logger.log_summary(result)

    def _build_node_record(self, explored: ExploredNode) -> NodeRecord:
        seconds_by_component = self._observations.seconds_by_component

        return NodeRecord(
            node_id=self._node_count,
            depth=len(explored.node.branching_decisions),
            compatible_column_count=self._observations.compatible_column_count,
            round_count=self._observations.round_count,
            new_column_count=self._observations.new_column_count,
            lower_bound=explored.node.lower_bound,
            outcome=explored.outcome,
            child_count=self._observations.child_count,
            integral=self._observations.integral,
            seconds_by_component=seconds_by_component,
            node_seconds=sum(seconds_by_component.values()),
            elapsed_seconds=perf_counter() - self._started_at,
            incumbent_objective=explored.incumbent_objective,
            best_bound=explored.best_bound,
        )
