from abc import ABC, abstractmethod

from template.solvers.branch_and_price_solver.node_context import NodeContext


class NodeLowerBoundGenerator(ABC):
    # a valid lower bound for the node; e.g. the relaxation objective, or its ceiling
    # when every objective coefficient is integer
    @abstractmethod
    def generate(self, context: NodeContext) -> float: ...
