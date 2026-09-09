from template.model.data.problem_data import ProblemData
from template.validation.validation_rule import ValidationRule


class ItemIdsMatchIndexRule(ValidationRule):
    def validate(self, problem_data: ProblemData) -> None:
        for index, item in enumerate(problem_data.items):
            if item.id != index:
                raise ValueError(
                    f"item ids: item at index {index} has id {item.id},"
                    " ids must equal the tuple index"
                )


class PositiveItemWeightsRule(ValidationRule):
    def validate(self, problem_data: ProblemData) -> None:
        for item in problem_data.items:
            if item.weight <= 0:
                raise ValueError(
                    "item weights: weight must be positive,"
                    f" got {item.weight} for item {item.id}"
                )
