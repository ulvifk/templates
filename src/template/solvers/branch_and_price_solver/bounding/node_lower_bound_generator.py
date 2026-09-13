from abc import ABC, abstractmethod

from template.solvers.branch_and_price_solver.branching.branch_node import BranchNode
from template.solvers.branch_and_price_solver.column_generation.column_generation_result import (
    ColumnGenerationResult,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)


class NodeLowerBoundGenerator(ABC):
    # a valid lower bound for the node after pricing converged on a feasible master;
    # called before the master is disposed; e.g. the relaxation bound, or its ceiling
    # when every objective coefficient is integer
    @abstractmethod
    def generate(
        self, node: BranchNode, master: MasterProblem, result: ColumnGenerationResult
    ) -> float: ...
