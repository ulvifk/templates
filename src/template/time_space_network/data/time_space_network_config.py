from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TimeSpaceNetworkConfig:
    discretization_minutes: int
