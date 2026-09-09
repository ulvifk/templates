from typing import ClassVar

from template.model.data.problem_data import ProblemData
from template.validation.validation_rule import ValidationRule


class Validation:
    rules: ClassVar[list[ValidationRule]] = []

    @staticmethod
    def validate(problem_data: ProblemData) -> None:
        for rule in Validation.rules:
            rule.validate(problem_data)
