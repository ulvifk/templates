import gurobipy

from template.model.data.problem_data import ProblemData


class MIPVariables:
    # per problem: one private container per variable family, [index] -> gurobipy.Var,
    # as an explicit dict, list, or nested list (not gurobipy.tupledict). The container
    # is never exposed: all access goes through a family-specific getter,
    # get_<family>(index). Construction lives in MIPVariablesFactory below.

    # Example:
    #
    # # [item id, machine id] -> item runs on machine
    # _assign: dict[tuple[int, int], gurobipy.Var]
    #
    # def __init__(self, assign: dict[tuple[int, int], gurobipy.Var]) -> None:
    #     self._assign = assign
    #
    # def get_assign(self, item_id: int, machine_id: int) -> gurobipy.Var:
    #     return self._assign[item_id, machine_id]

    ...


class MIPVariablesFactory:
    @staticmethod
    def build(model: gurobipy.Model, problem_data: ProblemData) -> MIPVariables:
        raise NotImplementedError(
            "One _build_<family>_vars(model, problem_data) per decision family, "
            "then return MIPVariables(...)."
        )

    # Example:
    #
    # @staticmethod
    # def build(model: gurobipy.Model, problem_data: ProblemData) -> MIPVariables:
    #     assign = MIPVariablesFactory._build_assign_vars(model, problem_data)
    #
    #     return MIPVariables(assign)
    #
    # @staticmethod
    # def _build_assign_vars(
    #     model: gurobipy.Model, problem_data: ProblemData
    # ) -> dict[tuple[int, int], gurobipy.Var]:
    #     assign: dict[tuple[int, int], gurobipy.Var] = {}
    #     for item in problem_data.items:
    #         for machine in problem_data.machines:
    #             assign[item.id, machine.id] = model.addVar(
    #                 vtype=GRB.BINARY, name=f"x_{item.id}_{machine.id}"
    #             )
    #
    #     return assign
