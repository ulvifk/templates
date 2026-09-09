import logging
import math
import time

from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution
from template.model.solve_result import SolveResult
from template.model.solve_status import SolveStatus
from template.solvers.branch_price.branch_node import BranchNode, is_pruned_by_incumbent
from template.solvers.branch_price.branch_price_config import BranchPriceConfig
from template.solvers.branch_price.branching_rule import (
    BranchingRule,
    MostFractionalResourceRule,
)
from template.solvers.branch_price.node_selector import NodeSelector
from template.solvers.column_generation.column import build_solution_from_columns
from template.solvers.column_generation.column_generation import ColumnGeneration
from template.solvers.column_generation.column_pool import ColumnPool
from template.solvers.column_generation.master_problem import MasterProblem
from template.solvers.column_generation.pricing_problem import KnapsackPricer
from template.solvers.solver import Solver

logger = logging.getLogger(__name__)


class BranchPriceSolver(Solver):
    """Branch and price: every node runs column generation on its own master, and the whole tree shares one column pool."""

    SOLVER_NAME = "branch-price"

    _config: BranchPriceConfig

    _problem_data: ProblemData
    _pool: ColumnPool
    _column_generation: ColumnGeneration
    _branching_rule: BranchingRule
    _selector: NodeSelector

    _incumbent: Solution | None
    _incumbent_objective: float
    _first_incumbent_seconds: float
    _root_bound: float
    _explored_node_count: int
    _started: float
    _deadline: float

    def __init__(self, config: BranchPriceConfig) -> None:
        self._config = config

    def solve(self, problem_data: ProblemData) -> SolveResult:
        self._initialize_search(problem_data)

        while time.perf_counter() < self._deadline:
            node = self._selector.pop()
            if node is None:
                break
            self._explored_node_count += 1

            master = self._build_master(node)
            keep_searching = self._explore_node(node, master)
            master.close()
            if not keep_searching:
                break

        return self._get_result()

    def _initialize_search(self, problem_data: ProblemData) -> None:
        self._problem_data = problem_data
        self._pool = ColumnPool()
        self._column_generation = ColumnGeneration(
            KnapsackPricer(problem_data), self._pool
        )
        self._branching_rule = MostFractionalResourceRule()
        self._selector = NodeSelector()

        self._incumbent = None
        self._incumbent_objective = math.inf
        self._first_incumbent_seconds = math.inf
        self._root_bound = 0.0
        self._explored_node_count = 0
        self._started = time.perf_counter()
        self._deadline = self._started + self._config.time_limit_seconds

        self._selector.push([BranchNode.root(problem_data)])

    def _build_master(self, node: BranchNode) -> MasterProblem:
        """Build a master over the shared pool whose rows enforce the node's resource use and assignment bounds."""
        raise NotImplementedError(
            "Return a MasterProblem over self._pool.get_columns() with the node's resource_use and assignment bounds as rows."
        )

    def _explore_node(self, node: BranchNode, master: MasterProblem) -> bool:
        """Whether the search can keep going; an unconverged node stops it."""
        result = self._column_generation.run(
            master, self._deadline - time.perf_counter()
        )
        node.lower_bound = max(node.lower_bound, result.bound)
        if self._explored_node_count == 1:
            self._root_bound = result.bound
        logger.info(
            f"node {self._explored_node_count} bound {node.lower_bound:.2f} "
            f"incumbent {self._incumbent_objective:.2f} columns {result.column_count} "
            f"at {self._get_elapsed():.1f}s"
        )

        if not result.converged:
            # The node keeps its parent's bound, so putting it back keeps the tree bound valid.
            self._selector.push([node])
            return False
        if self._is_pruned(node):
            return True

        if self._is_incumbent_node():
            self._generate_incumbent(node)
            if self._is_pruned(node):
                return True

        children = self._branching_rule.get_children(node, master.get_column_values())
        if not children:
            self._accept_incumbent(
                build_solution_from_columns(master.get_column_values())
            )
            return True

        self._selector.push(children)
        return True

    def _is_pruned(self, node: BranchNode) -> bool:
        return is_pruned_by_incumbent(
            node, self._incumbent_objective, self._config.bound_tolerance
        )

    def _is_incumbent_node(self) -> bool:
        """Attempt an incumbent at the first explored node and every interval nodes after it."""
        explored_after_first = self._explored_node_count - 1
        return explored_after_first % self._config.node_incumbent_interval == 0

    def _generate_incumbent(self, node: BranchNode) -> None:
        """A fresh master of the node's pool solved as an integer program; the LP master stays untouched for branching."""
        budget = min(
            self._config.incumbent_time_limit_seconds,
            self._deadline - time.perf_counter(),
        )
        if budget <= 0.0:
            return

        integer_master = self._build_master(node)
        if integer_master.solve_integer(budget):
            self._accept_incumbent(
                build_solution_from_columns(integer_master.get_column_values())
            )
        integer_master.close()

    def _accept_incumbent(self, solution: Solution) -> None:
        objective = float(len(solution.used_resource_ids))
        if objective >= self._incumbent_objective:
            return

        self._incumbent = solution
        self._incumbent_objective = objective
        self._first_incumbent_seconds = min(
            self._first_incumbent_seconds, self._get_elapsed()
        )
        logger.info(f"incumbent {objective:.0f} at {self._get_elapsed():.1f}s")

    def _get_result(self) -> SolveResult:
        best_bound = max(
            self._root_bound,
            min(self._selector.get_open_bound(), self._incumbent_objective),
        )
        if self._incumbent is None:
            return self._build_result(
                Solution(assignments=()), SolveStatus.NO_INCUMBENT, best_bound
            )

        status = SolveStatus.TIME_LIMIT
        if self._is_closed():
            status = SolveStatus.OPTIMAL
        return self._build_result(self._incumbent, status, best_bound)

    def _is_closed(self) -> bool:
        """No open node can still beat the incumbent."""
        open_bound = self._selector.get_open_bound()
        return open_bound >= self._incumbent_objective - self._config.bound_tolerance

    def _build_result(
        self, solution: Solution, status: SolveStatus, best_bound: float
    ) -> SolveResult:
        return SolveResult(
            problem_data=self._problem_data,
            solution=solution,
            solver_name=self.SOLVER_NAME,
            status=status,
            runtime_seconds=self._get_elapsed(),
            best_bound=best_bound,
            meta_data={
                "explored_node_count": self._explored_node_count,
                "root_bound": self._root_bound,
                "column_count": len(self._pool.get_columns()),
                "first_incumbent_seconds": self._first_incumbent_seconds,
            },
        )

    def _get_elapsed(self) -> float:
        return time.perf_counter() - self._started
