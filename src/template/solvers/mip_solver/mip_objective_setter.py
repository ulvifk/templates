import gurobipy
from gurobipy import GRB, quicksum

from template.model.data.problem_data import ProblemData
from template.solvers.mip_solver.mip_variables import MIPVariables


class MIPObjectiveSetter:
    @staticmethod
    def set_objective(
        model: gurobipy.Model,
        variables: MIPVariables,
        problem_data: ProblemData,
    ) -> None:
        model.setObjective(
            quicksum(
                variables.get_use(resource.id) for resource in problem_data.resources
            ),
            GRB.MINIMIZE,
        )
