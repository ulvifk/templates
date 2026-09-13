from abc import ABC, abstractmethod

import gurobipy

from template.model.data.problem_data import ProblemData
from template.solvers.mip_solver.mip_variables import MIPVariables


class MIPConstraintSetter(ABC):
    # one private _set_<constraint> per formulation constraint, never several in one
    # method; lhs and rhs built explicitly with the paper's sides,
    # model.addConstr(lhs <= rhs, name=...), equation cited in a one-line docstring
    @abstractmethod
    def set_constraints(
        self,
        model: gurobipy.Model,
        variables: MIPVariables,
        problem_data: ProblemData,
    ) -> None: ...


# Example:
#
# class AssignmentConstraintSetter(MIPConstraintSetter):
#     def set_constraints(
#         self,
#         model: gurobipy.Model,
#         variables: MIPVariables,
#         problem_data: ProblemData,
#     ) -> None:
#         self._set_each_item_assigned_once(model, variables, problem_data)
#
#     def _set_each_item_assigned_once(
#         self,
#         model: gurobipy.Model,
#         variables: MIPVariables,
#         problem_data: ProblemData,
#     ) -> None:
#         """Eq. 2: sum_j x_ij = 1, for each i."""
#         for item in problem_data.items:
#             lhs = quicksum(
#                 variables.get_assign(item.id, machine.id)
#                 for machine in problem_data.machines
#             )
#             rhs = 1
#
#             model.addConstr(lhs == rhs, name=f"assigned_once_{item.id}")
