import gurobipy
from gurobipy import GRB

from template.model.data.problem_data import ProblemData
from template.model.solution.assignment import Assignment
from template.model.solution.solution import Solution
from template.model.solve_result import SolveResult
from template.model.solve_status import SolveStatus
from template.solvers.mip_solver.mip_config import MIPConfig
from template.solvers.mip_solver.mip_constraint_setter import MIPConstraintSetter
from template.solvers.mip_solver.mip_objective_setter import MIPObjectiveSetter
from template.solvers.mip_solver.mip_variables import MIPVariables
from template.solvers.solver import Solver


class MIPSolver(Solver):
    SOLVER_NAME = "mip"

    config: MIPConfig

    def __init__(self, config: MIPConfig) -> None:
        self.config = config

    def solve(self, problem_data: ProblemData) -> SolveResult:
        with gurobipy.Env() as env, gurobipy.Model(env=env) as model:
            model.Params.TimeLimit = self.config.time_limit_seconds
            variables = MIPVariables.build(model, problem_data)
            MIPConstraintSetter.set_constraints(model, variables, problem_data)
            MIPObjectiveSetter.set_objective(model, variables, problem_data)

            model.optimize()

            return self._build_result(model, variables, problem_data)

    def _build_result(
        self,
        model: gurobipy.Model,
        variables: MIPVariables,
        problem_data: ProblemData,
    ) -> SolveResult:
        if model.SolCount == 0:
            return SolveResult(
                problem_data=problem_data,
                solution=Solution(assignments=()),
                solver_name=self.SOLVER_NAME,
                status=SolveStatus.NO_INCUMBENT,
                runtime_seconds=model.Runtime,
                best_bound=model.ObjBound,
                meta_data={"node_count": model.NodeCount},
            )

        return SolveResult(
            problem_data=problem_data,
            solution=self._extract_solution(variables, problem_data),
            solver_name=self.SOLVER_NAME,
            status=self._read_status(model),
            runtime_seconds=model.Runtime,
            best_bound=model.ObjBound,
            meta_data={"node_count": model.NodeCount},
        )

    def _read_status(self, model: gurobipy.Model) -> SolveStatus:
        if model.Status == GRB.OPTIMAL:
            return SolveStatus.OPTIMAL
        return SolveStatus.TIME_LIMIT

    def _extract_solution(
        self, variables: MIPVariables, problem_data: ProblemData
    ) -> Solution:
        assignments: list[Assignment] = []
        for resource in problem_data.resources:
            if variables.get_use(resource.id).X < 0.5:
                continue
            item_ids = self._extract_item_ids(variables, problem_data, resource.id)
            assignments.append(Assignment(resource_id=resource.id, item_ids=item_ids))
        return Solution(assignments=tuple(assignments))

    def _extract_item_ids(
        self,
        variables: MIPVariables,
        problem_data: ProblemData,
        resource_id: int,
    ) -> tuple[int, ...]:
        item_ids: list[int] = []
        for item in problem_data.items:
            if variables.get_assignment(item.id, resource_id).X > 0.5:
                item_ids.append(item.id)
        return tuple(item_ids)
