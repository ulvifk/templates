from template.model.data.problem_data import ProblemData
from template.model.data.problem_data_parser import ProblemDataParser


def test_json_round_trip_preserves_problem_data(
    valid_problem_data: ProblemData,
) -> None:
    text = ProblemDataParser.to_json(valid_problem_data)
    assert ProblemDataParser.from_json(text) == valid_problem_data
