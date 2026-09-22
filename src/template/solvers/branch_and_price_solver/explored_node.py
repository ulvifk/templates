from dataclasses import dataclass

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.column_generation.column_generation_result import (
    ColumnGenerationResult,
)
from template.solvers.branch_and_price_solver.node_outcome import NodeOutcome
from template.solvers.branch_and_price_solver.timing.node_step import NodeStep


@dataclass(frozen=True, slots=True)
class ExploredNode:
    """What the search did with one node, and where the node's time went."""

    node_id: int  # 1-based order of exploration
    node: BranchNode
    outcome: NodeOutcome

    compatible_column_count: int
    column_generation_result: ColumnGenerationResult
    child_count: int  # 0 when the node did not branch

    # [step] -> its seconds; a step the node never reached is absent
    seconds_by_step: dict[NodeStep, float]
    elapsed_seconds: float  # since the search started

    # the search bounds after the node
    incumbent_objective: float
    best_bound: float
