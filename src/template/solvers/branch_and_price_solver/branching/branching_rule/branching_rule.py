from abc import ABC, abstractmethod
from dataclasses import replace

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.branching.branching_decision import (
    BranchingDecision,
)


class BranchingRule(ABC):
    # returns the children that split the node's fractionality, read from the node's
    # master relaxation solution; only called when the master found the node
    # fractional
    @abstractmethod
    def get_children(self, node: BranchNode) -> list[BranchNode]: ...

    @staticmethod
    def _build_child(node: BranchNode, decision: BranchingDecision) -> BranchNode:
        return replace(
            node,
            branching_decisions=(*node.branching_decisions, decision),
            master_relaxation_solution={},
        )
