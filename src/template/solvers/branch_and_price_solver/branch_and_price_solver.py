import math
from abc import ABC, abstractmethod
from typing import Any

from template.constants import ZERO_TOLERANCE
from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution
from template.model.solve_result import SolveResult
from template.solvers.branch_and_price_solver.branch_and_price_config import (
    BranchAndPriceConfig,
)
from template.solvers.branch_and_price_solver.branching.branch_node import (
    BranchNode,
    BranchNodeFactory,
)
from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.column_generation_result import (
    ColumnGenerationResult,
)
from template.solvers.branch_and_price_solver.column_generation.column_generation_status import (
    ColumnGenerationStatus,
)
from template.solvers.branch_and_price_solver.column_generation.column_pool import (
    ColumnPool,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)
from template.solvers.branch_and_price_solver.explored_node import ExploredNode
from template.solvers.branch_and_price_solver.incumbent.incumbent import Incumbent
from template.solvers.branch_and_price_solver.node_context import NodeContext
from template.solvers.branch_and_price_solver.node_evaluation import NodeEvaluation
from template.solvers.branch_and_price_solver.node_outcome import NodeOutcome
from template.solvers.branch_and_price_solver.search_summary import SearchSummary
from template.solvers.branch_and_price_solver.timing.node_step import NodeStep
from template.solvers.branch_and_price_solver.timing.step_timer import StepTimer
from template.solvers.solver import Solver


class BranchAndPriceSolver(Solver, ABC):
    SOLVER_NAME = "branch-and-price"

    _config: BranchAndPriceConfig

    _problem_data: ProblemData
    _column_pool: ColumnPool

    _incumbent: Incumbent | None  # the best integer solution found so far
    _root_bound: float
    _explored_node_count: int

    _started_at: float
    _deadline: float

    def __init__(self, config: BranchAndPriceConfig) -> None:
        self._config = config

    def solve(self, problem_data: ProblemData) -> SolveResult:
        self._initialize_search(problem_data)

        while self._config.clock.now_seconds() < self._deadline:
            node = self._config.node_selector.pop()
            if node is None:
                break
            if self._is_closed_by_incumbent(node.lower_bound):
                continue

            explored = self._explore_node(node)
            self._notify_node_explored(explored)

        solution = self._extract_solution(self._get_incumbent_column_values())
        summary = self._build_search_summary()
        self._notify_search_finished(summary)

        return SolveResult(
            problem_data=self._problem_data,
            solution=solution,
            meta_data=self._build_meta_data(summary),
        )

    def _initialize_search(self, problem_data: ProblemData) -> None:
        self._problem_data = problem_data

        self._column_pool = ColumnPool()

        self._incumbent = None
        self._root_bound = -math.inf
        self._explored_node_count = 0

        self._started_at = self._config.clock.now_seconds()
        self._deadline = self._started_at + self._config.time_limit_seconds

        self._config.node_selector.push([BranchNodeFactory.build_root()])

    def _explore_node(self, node: BranchNode) -> ExploredNode:
        self._explored_node_count += 1
        step_timer = StepTimer(self._config.clock)

        columns = self._get_compatible_columns(node)
        master = self._config.master_problem_builder.build(columns)
        node.apply_to_master(master)
        step_timer.finish_step(NodeStep.BUILD_MASTER)

        pricing_problem = self._config.pricing_problem_builder.build()
        node.apply_to_pricing(pricing_problem)
        step_timer.finish_step(NodeStep.BUILD_PRICING)

        column_generation_result = self._config.column_generation.run(
            master, pricing_problem, self._column_pool, step_timer
        )
        pricing_problem.dispose()
        step_timer.finish_step(NodeStep.COLUMN_GENERATION)

        evaluation = self._evaluate_node(
            node, master, column_generation_result, step_timer
        )
        master.dispose()

        node.lower_bound = evaluation.lower_bound
        node.master_relaxation_solution = evaluation.relaxation_solution
        self._record_root_bound(evaluation.lower_bound)

        outcome = self._settle_node(evaluation)

        children: list[BranchNode] = []
        if outcome is NodeOutcome.BRANCHED:
            children = self._config.branching_rule.get_children(node)
            step_timer.finish_step(NodeStep.BRANCHING)
            self._config.node_selector.push(children)

        return ExploredNode(
            node_id=self._explored_node_count,
            node=node,
            outcome=outcome,
            compatible_column_count=len(columns),
            column_generation_result=column_generation_result,
            evaluation=evaluation,
            child_count=len(children),
            seconds_by_step=step_timer.get_seconds_by_step(),
            elapsed_seconds=self._config.clock.now_seconds() - self._started_at,
            incumbent_objective=self._get_incumbent_objective(),
            best_bound=self._get_best_bound(),
        )

    # reads what the node offers while its master is alive; changes no search state
    def _evaluate_node(
        self,
        node: BranchNode,
        master: MasterProblem,
        column_generation_result: ColumnGenerationResult,
        step_timer: StepTimer,
    ) -> NodeEvaluation:
        if column_generation_result.status is ColumnGenerationStatus.INFEASIBLE:
            return NodeEvaluation(
                feasible=False,
                relaxation_objective=math.inf,
                lower_bound=math.inf,
                relaxation_solution={},
                integral=False,
                incumbent=None,
            )

        context = NodeContext(
            node=node,
            master=master,
            column_generation_result=column_generation_result,
            incumbent_objective=self._get_incumbent_objective(),
        )

        relaxation_objective = column_generation_result.relaxation_objective
        relaxation_solution = master.get_master_relaxation_solution()
        lower_bound = self._config.node_lower_bound_generator.generate(context)
        step_timer.finish_step(NodeStep.LOWER_BOUND)

        integral = master.is_integral()
        step_timer.finish_step(NodeStep.INTEGRALITY)

        incumbent: Incumbent | None
        if integral:
            incumbent = Incumbent(relaxation_objective, relaxation_solution)
        else:
            incumbent = self._config.node_incumbent_generator.generate(context)
            step_timer.finish_step(NodeStep.INCUMBENT)

        return NodeEvaluation(
            feasible=True,
            relaxation_objective=relaxation_objective,
            lower_bound=lower_bound,
            relaxation_solution=relaxation_solution,
            integral=integral,
            incumbent=incumbent,
        )

    # takes the incumbent the node offers when it improves, and decides the node's fate;
    # an integral node is judged by its own objective, not by the generator's bound
    def _settle_node(self, evaluation: NodeEvaluation) -> NodeOutcome:
        if not evaluation.feasible:
            return NodeOutcome.INFEASIBLE

        improved = self._improves_incumbent(evaluation.incumbent)
        if improved:
            self._incumbent = evaluation.incumbent

        if evaluation.integral:
            return NodeOutcome.INTEGRAL if improved else NodeOutcome.PRUNED
        if self._is_closed_by_incumbent(evaluation.lower_bound):
            return NodeOutcome.HEURISTIC if improved else NodeOutcome.PRUNED

        return NodeOutcome.BRANCHED

    def _notify_node_explored(self, explored: ExploredNode) -> None:
        for observer in self._config.observers:
            observer.on_node_explored(explored)

    def _notify_search_finished(self, summary: SearchSummary) -> None:
        for observer in self._config.observers:
            observer.on_search_finished(summary)

    def _get_compatible_columns(self, node: BranchNode) -> list[Column]:
        return [
            column
            for column in self._column_pool.get_columns()
            if node.is_column_compatible(column)
        ]

    def _record_root_bound(self, bound: float) -> None:
        if self._explored_node_count == 1:
            self._root_bound = bound

    # the objective is minimized, so a bound that reaches the incumbent proves nothing
    # below it is left: a node with such a bound is pruned, a tree with such a bound
    # is solved
    def _is_closed_by_incumbent(self, bound: float) -> bool:
        return bound >= self._get_incumbent_objective() - ZERO_TOLERANCE

    def _is_better_than_incumbent(self, objective: float) -> bool:
        return objective < self._get_incumbent_objective() - ZERO_TOLERANCE

    def _improves_incumbent(self, incumbent: Incumbent | None) -> bool:
        if incumbent is None:
            return False

        return self._is_better_than_incumbent(incumbent.objective)

    def _get_incumbent_objective(self) -> float:
        if self._incumbent is None:
            return math.inf

        return self._incumbent.objective

    def _get_incumbent_column_values(self) -> dict[Column, float]:
        if self._incumbent is None:
            return {}

        return self._incumbent.column_values

    def _build_search_summary(self) -> SearchSummary:
        best_bound = self._get_best_bound()

        return SearchSummary(
            status=self._get_status(best_bound),
            objective=self._get_incumbent_objective(),
            best_bound=best_bound,
            root_bound=self._root_bound,
            explored_node_count=self._explored_node_count,
            column_count=len(self._column_pool.get_columns()),
            runtime_seconds=self._config.clock.now_seconds() - self._started_at,
        )

    def _build_meta_data(self, summary: SearchSummary) -> dict[str, Any]:
        return {
            "solver_name": self.SOLVER_NAME,
            "status": summary.status,
            "runtime_seconds": summary.runtime_seconds,
            "objective": summary.objective,
            "best_bound": summary.best_bound,
            "root_bound": summary.root_bound,
            "explored_node_count": summary.explored_node_count,
            "column_count": summary.column_count,
        }

    def _get_best_bound(self) -> float:
        open_bound = min(
            self._config.node_selector.get_best_lower_bound(),
            self._get_incumbent_objective(),
        )

        return max(self._root_bound, open_bound)

    def _get_status(self, best_bound: float) -> str:
        if self._incumbent is None:
            if self._config.node_selector.get_best_lower_bound() == math.inf:
                return "infeasible"

            return "time-limit"
        if self._is_closed_by_incumbent(best_bound):
            return "optimal"

        return "time-limit"

    # build the solution from the incumbent's column values, preserving its objective;
    # an empty mapping means no incumbent and yields the empty solution
    @abstractmethod
    def _extract_solution(self, column_values: dict[Column, float]) -> Solution: ...
