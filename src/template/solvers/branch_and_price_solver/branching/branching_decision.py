from abc import ABC, abstractmethod
from dataclasses import dataclass

from template.solvers.branch_and_price_solver.column_generation.column import Column


@dataclass(frozen=True, slots=True)
class BranchingDecision(ABC):
    """A branch choice interpreted by both the master and pricing builders."""

    # Whether this column can be used at the node; rows may constrain combinations
    # of columns without excluding any individual column.
    @abstractmethod
    def is_column_compatible(self, column: Column) -> bool: ...
