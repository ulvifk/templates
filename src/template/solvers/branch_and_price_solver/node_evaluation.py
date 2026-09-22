from dataclasses import dataclass

from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.incumbent.incumbent import Incumbent


@dataclass(frozen=True, slots=True)
class NodeEvaluation:
    """Everything read from a node's master before it was disposed."""

    feasible: bool
    relaxation_objective: float  # math.inf when infeasible
    lower_bound: float  # the generator's bound; math.inf when infeasible
    # [column] -> value in the node's relaxation; empty when infeasible
    relaxation_solution: dict[Column, float]
    integral: bool

    # the node's own integral solution, or what the incumbent generator found
    incumbent: Incumbent | None
