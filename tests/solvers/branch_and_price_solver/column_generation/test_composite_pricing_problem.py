from collections.abc import Hashable
from dataclasses import dataclass

from template.solvers.branch_and_price_solver.column_generation.column import Column
from template.solvers.branch_and_price_solver.column_generation.master.duals import (
    Duals,
)
from template.solvers.branch_and_price_solver.column_generation.pricing.composite_pricing_problem import (
    CompositePricingProblem,
)
from template.solvers.branch_and_price_solver.column_generation.pricing.pricing_problem import (
    PricingProblem,
)


@dataclass(frozen=True, slots=True)
class FakeColumn(Column):
    key: tuple[int, ...]

    def get_key(self) -> Hashable:
        return self.key


class RecordingPricingProblem(PricingProblem):
    _columns: list[Column]

    received_duals: list[Duals]
    disposed: bool

    def __init__(self, columns: list[Column]) -> None:
        self._columns = columns
        self.received_duals = []
        self.disposed = False

    def price(self, duals: Duals) -> list[Column]:
        self.received_duals.append(duals)
        return self._columns

    def dispose(self) -> None:
        self.disposed = True


def test_price_returns_first_seen_union_and_keeps_component_results_unchanged() -> None:
    first = FakeColumn(cost=1.0, key=(1,))
    duplicate = FakeColumn(cost=1.0, key=(1,))
    last = FakeColumn(cost=3.0, key=(2,))
    first_result: list[Column] = [first, duplicate]
    second_result: list[Column] = [duplicate, last]
    components = [
        RecordingPricingProblem(first_result),
        RecordingPricingProblem(second_result),
    ]
    composite = CompositePricingProblem(components)

    columns = composite.price(Duals())

    assert columns == [first, last]
    assert columns[0] is first
    assert columns is not first_result
    assert columns is not second_result
    assert first_result == [first, duplicate]
    assert second_result == [duplicate, last]


def test_price_calls_every_component_when_an_earlier_component_is_empty() -> None:
    column = FakeColumn(cost=1.0, key=(1,))
    first = RecordingPricingProblem([])
    second = RecordingPricingProblem([column])
    composite = CompositePricingProblem([first, second])

    columns = composite.price(Duals())

    assert columns == [column]
    assert len(first.received_duals) == 1
    assert len(second.received_duals) == 1


def test_price_passes_the_same_duals_to_every_component() -> None:
    duals = Duals()
    first = RecordingPricingProblem([])
    second = RecordingPricingProblem([])
    composite = CompositePricingProblem([first, second])

    composite.price(duals)

    assert first.received_duals == [duals]
    assert second.received_duals == [duals]
    assert first.received_duals[0] is duals
    assert second.received_duals[0] is duals


def test_get_pricing_problems_returns_the_owned_component_list() -> None:
    components = [RecordingPricingProblem([])]
    composite = CompositePricingProblem(components)

    assert composite.get_pricing_problems() is components


def test_dispose_disposes_every_component() -> None:
    first = RecordingPricingProblem([])
    second = RecordingPricingProblem([])
    composite = CompositePricingProblem([first, second])

    composite.dispose()

    assert first.disposed
    assert second.disposed
