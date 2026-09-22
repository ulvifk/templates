from dataclasses import dataclass

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.column_generation.column_generation_result import (
    ColumnGenerationResult,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)


@dataclass(frozen=True, slots=True)
class NodeContext:
    """What the node generators see about a feasible node once pricing converged."""

    node: BranchNode
    master: MasterProblem  # alive only during the generator calls
    column_generation_result: ColumnGenerationResult

    incumbent_objective: float  # the best objective so far; math.inf without one
