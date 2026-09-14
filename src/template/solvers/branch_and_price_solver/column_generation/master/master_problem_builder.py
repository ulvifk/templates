from abc import ABC, abstractmethod

from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)


class MasterProblemBuilder(ABC):
    # the restricted master over the compatible columns, with no decision applied; the
    # solver applies the node's decisions to it
    @abstractmethod
    def build(self, columns: list[Column]) -> MasterProblem: ...
