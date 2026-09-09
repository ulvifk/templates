from enum import Enum


class SolveStatus(Enum):
    OPTIMAL = "optimal"
    TIME_LIMIT = "time-limit"
    NO_INCUMBENT = "no-incumbent"
