from enum import Enum


class NodeStep(Enum):
    """The timed steps of a node in exploration order; the value is its table header."""

    BUILD_MASTER = "m_build"
    BUILD_PRICING = "p_build"
    MASTER_SOLVE = "master"
    PRICING = "pricing"
    COLUMN_GENERATION = "colgen"  # column generation outside master solves and pricing
    LOWER_BOUND = "lb"
    INTEGRALITY = "integ"
    INCUMBENT = "incumb"
    BRANCHING = "branch"
