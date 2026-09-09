from template.model.data.problem_data import ProblemData
from template.validation.validation_rule import ValidationRule


class ResourceIdsMatchIndexRule(ValidationRule):
    def validate(self, problem_data: ProblemData) -> None:
        for index, resource in enumerate(problem_data.resources):
            if resource.id != index:
                raise ValueError(
                    f"resource ids: resource at index {index} has id {resource.id},"
                    " ids must equal the tuple index"
                )


class PositiveResourceCapacitiesRule(ValidationRule):
    def validate(self, problem_data: ProblemData) -> None:
        for resource in problem_data.resources:
            if resource.capacity <= 0:
                raise ValueError(
                    "resource capacities: capacity must be positive,"
                    f" got {resource.capacity} for resource {resource.id}"
                )
