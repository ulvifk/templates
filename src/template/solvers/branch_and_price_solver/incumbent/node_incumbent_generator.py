from abc import ABC, abstractmethod

from template.solvers.branch_and_price_solver.incumbent.incumbent import Incumbent
from template.solvers.branch_and_price_solver.node_context import NodeContext


class NodeIncumbentGenerator(ABC):
    # a primal heuristic on a fractional node; e.g. solve the restricted master as an
    # integer program; None when it found nothing
    @abstractmethod
    def generate(self, context: NodeContext) -> Incumbent | None: ...
