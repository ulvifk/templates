from abc import ABC, abstractmethod

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.node_evaluation import NodeEvaluation


class BranchingRule(ABC):
    # returns the children that split the node's fractionality, read from the
    # evaluation's relaxation solution; only called on a fractional node; a child
    # appends its decision to the node's and inherits the node's bound
    @abstractmethod
    def get_children(
        self, node: BranchNode, evaluation: NodeEvaluation
    ) -> list[BranchNode]: ...
