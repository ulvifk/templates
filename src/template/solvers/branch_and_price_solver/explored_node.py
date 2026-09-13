from dataclasses import dataclass

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.node_outcome import NodeOutcome


@dataclass(frozen=True, slots=True)
class ExploredNode:
    """What the search did with one node."""

    node: BranchNode
    outcome: NodeOutcome

    # the search bounds after the node
    incumbent_objective: float
    best_bound: float
