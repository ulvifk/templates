from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ColumnGenerationResult:
    # trusted as a node bound only when converged
    bound: float
    converged: bool

    rounds: int
    column_count: int
    master_seconds: float
    pricing_seconds: float
