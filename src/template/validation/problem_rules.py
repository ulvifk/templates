from template.model.data.problem_data import ProblemData
from template.validation.validation_rule import ValidationRule


class ItemsExistRule(ValidationRule):
    def validate(self, problem_data: ProblemData) -> None:
        if len(problem_data.items) == 0:
            raise ValueError("items: problem data must contain at least one item")


class ResourcesExistRule(ValidationRule):
    def validate(self, problem_data: ProblemData) -> None:
        if len(problem_data.resources) == 0:
            raise ValueError(
                "resources: problem data must contain at least one resource"
            )
