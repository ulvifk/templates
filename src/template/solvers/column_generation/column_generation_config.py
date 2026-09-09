from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ColumnGenerationConfig:
    time_limit_seconds: float
    integer_time_limit_seconds: float
