import pytest

from template.model.data.item import Item
from template.model.data.problem_data import ProblemData
from template.model.data.resource import Resource


@pytest.fixture
def valid_problem_data() -> ProblemData:
    items = (
        Item(id=0, weight=3),
        Item(id=1, weight=4),
        Item(id=2, weight=5),
    )
    resources = (
        Resource(id=0, capacity=7),
        Resource(id=1, capacity=7),
    )
    return ProblemData(items=items, resources=resources)
