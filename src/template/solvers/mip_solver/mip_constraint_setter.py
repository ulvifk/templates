import gurobipy
from gurobipy import quicksum

from template.model.data.problem_data import ProblemData
from template.solvers.mip_solver.mip_variables import MIPVariables


class MIPConstraintSetter:
    @staticmethod
    def set_constraints(
        model: gurobipy.Model,
        variables: MIPVariables,
        problem_data: ProblemData,
    ) -> None:
        for item in problem_data.items:
            model.addConstr(
                quicksum(
                    variables.get_assignment(item.id, resource.id)
                    for resource in problem_data.resources
                )
                == 1,
                name=f"assign_once[{item.id}]",
            )

        for resource in problem_data.resources:
            model.addConstr(
                quicksum(
                    item.weight * variables.get_assignment(item.id, resource.id)
                    for item in problem_data.items
                )
                <= resource.capacity * variables.get_use(resource.id),
                name=f"capacity[{resource.id}]",
            )

        for item in problem_data.items:
            for resource in problem_data.resources:
                model.addConstr(
                    variables.get_assignment(item.id, resource.id)
                    <= variables.get_use(resource.id),
                    name=f"assign_needs_use[{item.id},{resource.id}]",
                )
