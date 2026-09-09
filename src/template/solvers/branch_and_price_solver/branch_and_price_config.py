from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BranchAndPriceConfig:
    time_limit_seconds: float
