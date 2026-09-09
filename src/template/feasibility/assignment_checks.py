from collections import Counter

from template.feasibility.feasibility_check import FeasibilityCheck
from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution


class EveryItemAssignedOnceCheck(FeasibilityCheck):
    def check(self, solution: Solution, problem_data: ProblemData) -> None:
        counts = Counter(solution.assigned_item_ids)
        for item in problem_data.items:
            if counts[item.id] != 1:
                raise ValueError(
                    f"item assignment: item {item.id} is assigned"
                    f" {counts[item.id]} times, expected exactly once"
                )


class AssignedItemsExistCheck(FeasibilityCheck):
    def check(self, solution: Solution, problem_data: ProblemData) -> None:
        known_item_ids = {item.id for item in problem_data.items}
        for item_id in solution.assigned_item_ids:
            if item_id not in known_item_ids:
                raise ValueError(f"item assignment: unknown item {item_id}")


class UsedResourcesExistCheck(FeasibilityCheck):
    def check(self, solution: Solution, problem_data: ProblemData) -> None:
        known_resource_ids = {resource.id for resource in problem_data.resources}
        for resource_id in solution.used_resource_ids:
            if resource_id not in known_resource_ids:
                raise ValueError(f"resource usage: unknown resource {resource_id}")
