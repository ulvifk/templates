from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MIPConfig:
    time_limit_seconds: float
