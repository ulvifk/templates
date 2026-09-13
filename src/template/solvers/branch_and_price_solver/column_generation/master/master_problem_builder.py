from abc import ABC, abstractmethod

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)


class MasterProblemBuilder(ABC):
    # Build the master with all supplied compatible columns and apply
    # node.branching_decisions to its formulation.
    @abstractmethod
    def build(self, node: BranchNode, columns: list[Column]) -> MasterProblem: ...
