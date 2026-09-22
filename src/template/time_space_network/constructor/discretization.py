import math

from template.constants import ZERO_TOLERANCE


# a minute within ZERO_TOLERANCE steps of a grid minute snaps to it, so float noise
# never pushes a value onto the next or previous step
def ceil_to_step(minutes: float, discretization_minutes: int) -> int:
    steps = math.ceil(minutes / discretization_minutes - ZERO_TOLERANCE)
    return steps * discretization_minutes


def floor_to_step(minutes: float, discretization_minutes: int) -> int:
    steps = math.floor(minutes / discretization_minutes + ZERO_TOLERANCE)
    return steps * discretization_minutes
