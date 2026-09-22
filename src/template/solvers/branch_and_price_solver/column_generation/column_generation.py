from abc import ABC, abstractmethod

from template.solvers.branch_and_price_solver.column_generation.column_generation_result import (
    ColumnGenerationResult,
)
from template.solvers.branch_and_price_solver.column_generation.column_pool import (
    ColumnPool,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)
from template.solvers.branch_and_price_solver.column_generation.pricing.pricing_problem import (
    PricingProblem,
)
from template.solvers.branch_and_price_solver.timing.step_timer import StepTimer


class ColumnGeneration(ABC):
    # Solve, price, and add columns until pricing certifies convergence; finish each
    # master solve as MASTER_SOLVE and each pricing call as PRICING on the step timer.
    @abstractmethod
    def run(
        self,
        master: MasterProblem,
        pricing_problem: PricingProblem,
        column_pool: ColumnPool,
        step_timer: StepTimer,
    ) -> ColumnGenerationResult: ...
