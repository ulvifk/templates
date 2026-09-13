from dataclasses import dataclass

from template.solvers.branch_and_price_solver.node_outcome import NodeOutcome
from template.solvers.branch_and_price_solver.progress.node_component import (
    NodeComponent,
)


@dataclass(frozen=True, slots=True)
class NodeRecord:
    """Everything logged about one explored node."""

    node_id: int  # 1-based order of exploration
    depth: int

    compatible_column_count: int
    round_count: int
    new_column_count: int
    lower_bound: float  # inf when the node is infeasible
    outcome: NodeOutcome
    child_count: int  # 0 when the node did not branch
    integral: bool | None  # absent when the node was infeasible

    # [component] -> its seconds; a component the node never reached is absent
    seconds_by_component: dict[NodeComponent, float]
    node_seconds: float
    elapsed_seconds: float  # since the search started

    incumbent_objective: float
    best_bound: float
