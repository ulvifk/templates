import gurobipy

from template.model.data.problem_data import ProblemData
from template.solvers.mip_solver.mip_variables import MIPVariables


class MIPObjectiveSetter:
    @staticmethod
    def set_objective(
        model: gurobipy.Model,
        variables: MIPVariables,
        problem_data: ProblemData,
    ) -> None:
        raise NotImplementedError(
            "model.setObjective(<expression>, GRB.MINIMIZE or GRB.MAXIMIZE)."
        )

    # Example:
    #
    # @staticmethod
    # def set_objective(
    #     model: gurobipy.Model,
    #     variables: MIPVariables,
    #     problem_data: ProblemData,
    # ) -> None:
    #     """Eq. 1: min sum_ij c_ij x_ij."""
    #     cost_terms = []
    #     for item in problem_data.items:
    #         for machine in problem_data.machines:
    #             cost = problem_data.cost[item.id, machine.id]
    #             assign = variables.get_assign(item.id, machine.id)
    #             cost_terms.append(cost * assign)
    #
    #     total_cost = quicksum(cost_terms)
    #
    #     model.setObjective(total_cost, GRB.MINIMIZE)
