from enum import Enum


class ColumnGenerationStatus(Enum):
    CONVERGED = "converged"
    INFEASIBLE = "infeasible"
