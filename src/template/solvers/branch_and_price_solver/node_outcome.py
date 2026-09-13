from enum import Enum


class NodeOutcome(Enum):
    BRANCHED = "branched"
    PRUNED = "pruned"
    INTEGRAL = "integral"
    HEURISTIC = "heuristic"
    INFEASIBLE = "infeasible"
