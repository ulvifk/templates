from abc import ABC, abstractmethod

import gurobipy

from template.model.data.problem_data import ProblemData
from template.solvers.mip_solver.mip_variables import MIPVariables


class MIPObjectiveSetter(ABC):
    # model.setObjective(expr, GRB.MINIMIZE | GRB.MAXIMIZE)
    @abstractmethod
    def set_objective(
        self,
        model: gurobipy.Model,
        variables: MIPVariables,
        problem_data: ProblemData,
    ) -> None: ...


# Example:
#
# class AssignmentObjectiveSetter(MIPObjectiveSetter):
#     def set_objective(
#         self,
#         model: gurobipy.Model,
#         variables: MIPVariables,
#         problem_data: ProblemData,
#     ) -> None:
#         """Eq. 1: min sum_ij c_ij x_ij."""
#         cost_terms = []
#         for item in problem_data.items:
#             for machine in problem_data.machines:
#                 cost = problem_data.cost[item.id, machine.id]
#                 assign = variables.get_assign(item.id, machine.id)
#                 cost_terms.append(cost * assign)
#
#         total_cost = quicksum(cost_terms)
#
#         model.setObjective(total_cost, GRB.MINIMIZE)
