import gurobipy

from template.model.data.problem_data import ProblemData
from template.solvers.mip_solver.mip_variables import MIPVariables


class MIPConstraintSetter:
    @staticmethod
    def set_constraints(
        model: gurobipy.Model,
        variables: MIPVariables,
        problem_data: ProblemData,
    ) -> None:
        raise NotImplementedError(
            "Call one _set_<constraint>(model, variables, problem_data) per "
            "formulation constraint, never several constraints in one method; "
            "each builds lhs and rhs explicitly, adds model.addConstr(lhs <= rhs, "
            "name=...) rows, and cites its equation in a one-line docstring."
        )

    # Example:
    #
    # @staticmethod
    # def set_constraints(
    #     model: gurobipy.Model,
    #     variables: MIPVariables,
    #     problem_data: ProblemData,
    # ) -> None:
    #     MIPConstraintSetter._set_each_item_assigned_once(
    #         model, variables, problem_data
    #     )
    #
    # @staticmethod
    # def _set_each_item_assigned_once(
    #     model: gurobipy.Model,
    #     variables: MIPVariables,
    #     problem_data: ProblemData,
    # ) -> None:
    #     """Eq. 2: sum_j x_ij = 1, for each i."""
    #     for item in problem_data.items:
    #         lhs = quicksum(
    #             variables.get_assign(item.id, machine.id)
    #             for machine in problem_data.machines
    #         )
    #         rhs = 1
    #
    #         model.addConstr(lhs == rhs, name=f"assigned_once_{item.id}")
