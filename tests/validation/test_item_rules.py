import pytest

from template.model.data.item import Item
from template.model.data.problem_data import ProblemData
from template.validation.item_rules import (
    ItemIdsMatchIndexRule,
    PositiveItemWeightsRule,
)


@pytest.fixture
def problem_data_with_misindexed_item(valid_problem_data: ProblemData) -> ProblemData:
    items = (valid_problem_data.items[0], Item(id=7, weight=4))
    return ProblemData(items=items, resources=valid_problem_data.resources)


@pytest.fixture
def problem_data_with_zero_weight_item(valid_problem_data: ProblemData) -> ProblemData:
    items = (valid_problem_data.items[0], Item(id=1, weight=0))
    return ProblemData(items=items, resources=valid_problem_data.resources)


def test_item_ids_match_index_accepts_valid_data(
    valid_problem_data: ProblemData,
) -> None:
    ItemIdsMatchIndexRule().validate(valid_problem_data)


def test_item_ids_match_index_rejects_misindexed_item(
    problem_data_with_misindexed_item: ProblemData,
) -> None:
    with pytest.raises(ValueError, match="item ids"):
        ItemIdsMatchIndexRule().validate(problem_data_with_misindexed_item)


def test_positive_item_weights_accepts_valid_data(
    valid_problem_data: ProblemData,
) -> None:
    PositiveItemWeightsRule().validate(valid_problem_data)


def test_positive_item_weights_rejects_zero_weight(
    problem_data_with_zero_weight_item: ProblemData,
) -> None:
    with pytest.raises(ValueError, match="item weights"):
        PositiveItemWeightsRule().validate(problem_data_with_zero_weight_item)
