from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BranchPriceConfig:
    time_limit_seconds: float

    node_incumbent_interval: int
    incumbent_time_limit_seconds: float
    bound_tolerance: float
