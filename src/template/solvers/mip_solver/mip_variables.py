class MIPVariables:
    # per problem: one private container per variable family, [index] -> gurobipy.Var,
    # as an explicit dict, list, or nested list (not gurobipy.tupledict). The container
    # is never exposed: all access goes through a family-specific getter,
    # get_<family>(index).

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
