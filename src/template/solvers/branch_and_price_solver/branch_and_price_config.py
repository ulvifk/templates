from dataclasses import dataclass

from template.solvers.branch_and_price_solver.bounding.node_lower_bound_generator import (
    NodeLowerBoundGenerator,
)
from template.solvers.branch_and_price_solver.branch_and_price_observer import (
    BranchAndPriceObserver,
)
from template.solvers.branch_and_price_solver.branching.branching_rule.branching_rule import (
    BranchingRule,
)
from template.solvers.branch_and_price_solver.branching.node_selector.node_selector import (
    NodeSelector,
)
from template.solvers.branch_and_price_solver.column_generation.column_generation import (
    ColumnGeneration,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem_builder import (
    MasterProblemBuilder,
)
from template.solvers.branch_and_price_solver.column_generation.pricing.pricing_problem_builder import (
    PricingProblemBuilder,
)
from template.solvers.branch_and_price_solver.incumbent.node_incumbent_generator import (
    NodeIncumbentGenerator,
)
from template.solvers.branch_and_price_solver.timing.clock import Clock


@dataclass(frozen=True, slots=True)
class BranchAndPriceConfig:
    time_limit_seconds: float
    clock: Clock

    node_selector: NodeSelector
    branching_rule: BranchingRule
    master_problem_builder: MasterProblemBuilder
    pricing_problem_builder: PricingProblemBuilder
    column_generation: ColumnGeneration
    node_lower_bound_generator: NodeLowerBoundGenerator
    node_incumbent_generator: NodeIncumbentGenerator

    observers: list[BranchAndPriceObserver]
