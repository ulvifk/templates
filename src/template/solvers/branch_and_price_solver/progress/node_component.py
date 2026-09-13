from enum import Enum


class NodeComponent(Enum):
    MASTER = "master"
    PRICING = "pricing"
    COLUMN_GENERATION = "column_generation"
    LOWER_BOUND = "lower_bound"
    INTEGRALITY = "integrality"
    INCUMBENT = "incumbent"
    BRANCHING = "branching"
