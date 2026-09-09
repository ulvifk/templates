from template.feasibility.feasibility_check import FeasibilityCheck
from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution


class CapacityCheck(FeasibilityCheck):
    def check(self, solution: Solution, problem_data: ProblemData) -> None:
        for assignment in solution.assignments:
            resource = problem_data.resources[assignment.resource_id]
            total_weight = sum(
                problem_data.items[item_id].weight for item_id in assignment.item_ids
            )
            if total_weight > resource.capacity + self.TOLERANCE:
                raise ValueError(
                    f"capacity: resource {resource.id} carries weight"
                    f" {total_weight} above capacity {resource.capacity}"
                )
