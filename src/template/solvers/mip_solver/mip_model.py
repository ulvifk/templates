from abc import ABC, abstractmethod

import gurobipy

from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution
from template.solvers.mip_solver.mip_constraint_setter import MIPConstraintSetter
from template.solvers.mip_solver.mip_objective_setter import MIPObjectiveSetter
from template.solvers.mip_solver.mip_variables import MIPVariables


class MIPModel(ABC):
    _constraint_setter: MIPConstraintSetter
    _objective_setter: MIPObjectiveSetter

    env: gurobipy.Env
    model: gurobipy.Model
    _variables: MIPVariables

    def __init__(
        self,
        constraint_setter: MIPConstraintSetter,
        objective_setter: MIPObjectiveSetter,
    ) -> None:
        self._constraint_setter = constraint_setter
        self._objective_setter = objective_setter

        self.env = gurobipy.Env(empty=True)

    # the environment must be started before this runs; then variables,
    # constraints, objective, in that order
    def build(self, problem_data: ProblemData) -> None:
        self.model = gurobipy.Model(env=self.env)

        self._variables = self._build_variables(self.model, problem_data)

        self._constraint_setter.set_constraints(
            self.model, self._variables, problem_data
        )
        self._objective_setter.set_objective(self.model, self._variables, problem_data)

    # read self._variables values into a Solution: binaries above 0.5, continuous
    # rounded
    @abstractmethod
    def extract_solution(self, problem_data: ProblemData) -> Solution: ...

    # one private _build_<family>_vars per decision family, then MIPVariables(...)
    @abstractmethod
    def _build_variables(
        self, model: gurobipy.Model, problem_data: ProblemData
    ) -> MIPVariables: ...


# Example:
#
# class AssignmentMIPModel(MIPModel):
#     def extract_solution(self, problem_data: ProblemData) -> Solution:
#         assignments = {}
#         for item in problem_data.items:
#             for machine in problem_data.machines:
#                 if self._variables.get_assign(item.id, machine.id).X > 0.5:
#                     assignments[item.id] = machine.id
#
#         return Solution(assignments)
#
#     def _build_variables(
#         self, model: gurobipy.Model, problem_data: ProblemData
#     ) -> MIPVariables:
#         assign = self._build_assign_vars(model, problem_data)
#
#         return MIPVariables(assign)
#
#     def _build_assign_vars(
#         self, model: gurobipy.Model, problem_data: ProblemData
#     ) -> dict[tuple[int, int], gurobipy.Var]:
#         assign: dict[tuple[int, int], gurobipy.Var] = {}
#         for item in problem_data.items:
#             for machine in problem_data.machines:
#                 assign[item.id, machine.id] = model.addVar(
#                     vtype=GRB.BINARY, name=f"x_{item.id}_{machine.id}"
#                 )
#
#         return assign
