from collections.abc import Hashable

from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.master.duals import (
    Duals,
)
from template.solvers.branch_and_price_solver.column_generation.pricing.pricing_problem import (
    PricingProblem,
)


class CompositePricingProblem[P: PricingProblem](PricingProblem):
    """A nonempty group of distinct pricers covering the full pricing domain."""

    _pricing_problems: list[P]

    def __init__(self, pricing_problems: list[P]) -> None:
        self._pricing_problems = pricing_problems

    def get_pricing_problems(self) -> list[P]:
        return self._pricing_problems

    def price(self, duals: Duals) -> list[Column]:
        columns: list[Column] = []
        column_keys: set[Hashable] = set()

        for pricing_problem in self._pricing_problems:
            priced_columns = pricing_problem.price(duals)
            for column in priced_columns:
                key = column.get_key()
                if key in column_keys:
                    continue

                column_keys.add(key)
                columns.append(column)

        return columns

    def dispose(self) -> None:
        for pricing_problem in self._pricing_problems:
            pricing_problem.dispose()
