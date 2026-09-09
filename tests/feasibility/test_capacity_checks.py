import pytest

from template.feasibility.capacity_checks import CapacityCheck
from template.model.data.problem_data import ProblemData
from template.model.solution.assignment import Assignment
from template.model.solution.solution import Solution


@pytest.fixture
def feasible_solution() -> Solution:
    return Solution(
        assignments=(
            Assignment(resource_id=0, item_ids=(0, 1)),
            Assignment(resource_id=1, item_ids=(2,)),
        )
    )


@pytest.fixture
def overloaded_solution() -> Solution:
    return Solution(assignments=(Assignment(resource_id=0, item_ids=(0, 1, 2)),))


def test_capacity_accepts_feasible_solution(
    feasible_solution: Solution, valid_problem_data: ProblemData
) -> None:
    CapacityCheck().check(feasible_solution, valid_problem_data)


def test_capacity_rejects_overloaded_resource(
    overloaded_solution: Solution, valid_problem_data: ProblemData
) -> None:
    with pytest.raises(ValueError, match="capacity"):
        CapacityCheck().check(overloaded_solution, valid_problem_data)
