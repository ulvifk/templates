from dataclasses import dataclass

import gurobipy
from gurobipy import GRB

from template.model.data.problem_data import ProblemData


@dataclass(frozen=True, slots=True)
class MIPVariables:
    use: dict[int, gurobipy.Var]  # [resource id] -> resource is used
    assign: dict[
        tuple[int, int], gurobipy.Var
    ]  # [item id, resource id] -> item sits on resource

    @staticmethod
    def build(model: gurobipy.Model, problem_data: ProblemData) -> MIPVariables:
        use: dict[int, gurobipy.Var] = {}
        for resource in problem_data.resources:
            use[resource.id] = model.addVar(
                vtype=GRB.BINARY, name=f"use[{resource.id}]"
            )

        assign: dict[tuple[int, int], gurobipy.Var] = {}
        for item in problem_data.items:
            for resource in problem_data.resources:
                assign[item.id, resource.id] = model.addVar(
                    vtype=GRB.BINARY, name=f"assign[{item.id},{resource.id}]"
                )

        return MIPVariables(use=use, assign=assign)

    def get_use(self, resource_id: int) -> gurobipy.Var:
        return self.use[resource_id]

    def get_assignment(self, item_id: int, resource_id: int) -> gurobipy.Var:
        return self.assign[item_id, resource_id]
