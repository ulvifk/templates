import math
from collections.abc import Hashable
from dataclasses import dataclass

import pytest

from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.column_generation_status import (
    ColumnGenerationStatus,
)
from template.solvers.branch_and_price_solver.column_generation.column_pool import (
    ColumnPool,
)
from template.solvers.branch_and_price_solver.column_generation.master.duals import (
    Duals,
)
from template.solvers.branch_and_price_solver.column_generation.master.master_problem import (
    MasterProblem,
)
from template.solvers.branch_and_price_solver.column_generation.pricing.pricing_problem import (
    PricingProblem,
)
from template.solvers.branch_and_price_solver.column_generation.standard_column_generation import (
    StandardColumnGeneration,
)


@dataclass(frozen=True, slots=True)
class FakeColumn(Column):
    key: tuple[int, ...]

    def get_key(self) -> Hashable:
        return self.key


class ScriptedMasterProblem(MasterProblem):
    _objectives: list[float]
    _solve_count: int
    _feasible: bool

    added_columns: list[Column]

    def __init__(self, objectives: list[float], feasible: bool = True) -> None:
        self._objectives = objectives
        self._solve_count = 0
        self._feasible = feasible

        self.added_columns = []

    def add_columns(self, columns: list[Column]) -> None:
        self.added_columns += columns

    def solve_relaxation(self) -> float:
        objective = self._objectives[self._solve_count]
        self._solve_count += 1

        return objective

    def get_duals(self) -> Duals:
        return Duals()

    def is_feasible(self) -> bool:
        return self._feasible

    def is_integral(self) -> bool:
        return False

    def get_master_relaxation_solution(self) -> dict[Column, float]:
        return {}

    def dispose(self) -> None:
        return None


class ScriptedPricingProblem(PricingProblem):
    _priced_batches: list[list[Column]]
    _price_count: int
    disposed: bool

    def __init__(self, priced_batches: list[list[Column]]) -> None:
        self._priced_batches = priced_batches
        self._price_count = 0
        self.disposed = False

    def price(self, duals: Duals) -> list[Column]:
        batch = self._priced_batches[self._price_count]
        self._price_count += 1

        return batch

    def dispose(self) -> None:
        self.disposed = True


def test_column_generation_converges_after_pricing_returns_no_columns() -> None:
    column = FakeColumn(cost=101.0, key=(1,))
    master = ScriptedMasterProblem([201.0, 101.0])
    pricer = ScriptedPricingProblem([[column], []])

    result = StandardColumnGeneration().run(master, pricer, ColumnPool())

    assert result.status is ColumnGenerationStatus.CONVERGED
    assert result.bound == 101.0
    assert result.round_count == 2
    assert master.added_columns == [column]


def test_pricing_convergence_with_an_infeasible_master_is_infeasible() -> None:
    master = ScriptedMasterProblem([1.0], feasible=False)
    pricer = ScriptedPricingProblem([[]])

    result = StandardColumnGeneration().run(master, pricer, ColumnPool())

    assert result.status is ColumnGenerationStatus.INFEASIBLE
    assert result.bound == math.inf
    assert result.round_count == 1


def test_only_known_columns_raise_instead_of_certifying_convergence() -> None:
    known = FakeColumn(cost=1.0, key=(1,))
    pool = ColumnPool()
    pool.add([known])
    master = ScriptedMasterProblem([0.0])
    pricer = ScriptedPricingProblem([[known]])

    with pytest.raises(RuntimeError, match="only known columns"):
        StandardColumnGeneration().run(master, pricer, pool)


def test_duplicate_columns_are_deduplicated_before_reaching_the_master() -> None:
    known = FakeColumn(cost=1.0, key=(1,))
    fresh = FakeColumn(cost=2.0, key=(2,))
    pool = ColumnPool()
    pool.add([known])
    master = ScriptedMasterProblem([20.0, 15.0])
    pricer = ScriptedPricingProblem([[known, fresh], []])

    result = StandardColumnGeneration().run(master, pricer, pool)

    assert result.status is ColumnGenerationStatus.CONVERGED
    assert master.added_columns == [fresh]
