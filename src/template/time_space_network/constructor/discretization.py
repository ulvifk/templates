import math


def ceil_to_step(minutes: float, discretization_minutes: int) -> int:
    return math.ceil(minutes / discretization_minutes) * discretization_minutes


def floor_to_step(minutes: float, discretization_minutes: int) -> int:
    return math.floor(minutes / discretization_minutes) * discretization_minutes
