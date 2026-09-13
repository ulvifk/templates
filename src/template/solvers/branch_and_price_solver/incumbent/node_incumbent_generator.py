from abc import ABC, abstractmethod

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)
from template.solvers.branch_and_price_solver.incumbent.incumbent import Incumbent


class NodeIncumbentGenerator(ABC):
    # a primal heuristic on a fractional node, run while the master is alive; e.g.
    # solve the restricted master as an integer program; None when it found nothing
    @abstractmethod
    def generate(self, node: BranchNode, master: MasterProblem) -> Incumbent | None: ...
