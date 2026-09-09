from abc import ABC, abstractmethod

from template.model.data.problem_data import ProblemData


class ValidationRule(ABC):
    @abstractmethod
    def validate(self, problem_data: ProblemData) -> None: ...
