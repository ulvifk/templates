from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SearchSummary:
    """How the search ended."""

    status: str  # "optimal", "infeasible", or "time-limit"
    objective: float  # math.inf without an incumbent
    best_bound: float
    root_bound: float

    explored_node_count: int
    column_count: int
    runtime_seconds: float
