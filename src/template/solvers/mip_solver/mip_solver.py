from typing import Any

from gurobipy import GRB

from template.model.data.problem_data import ProblemData
from template.model.solution.solution import SolutionFactory
from template.model.solve_result import SolveResult
from template.solvers.mip_solver.mip_config import MIPConfig
from template.solvers.mip_solver.mip_model import MIPModel
from template.solvers.solver import Solver


class MIPSolver(Solver):
    SOLVER_NAME = "mip"

    _config: MIPConfig
    _mip_model: MIPModel

    def __init__(self, config: MIPConfig, mip_model: MIPModel) -> None:
        self._config = config
        self._mip_model = mip_model

    def solve(self, problem_data: ProblemData) -> SolveResult:
        self._configure()
        self._mip_model.build(problem_data)

        self._mip_model.model.optimize()
        self._raise_if_model_is_infeasible()

        return self._build_result(problem_data)

    def _configure(self) -> None:
        env = self._mip_model.env

        env.setParam("TimeLimit", self._config.time_limit_seconds)
        env.start()

    def _raise_if_model_is_infeasible(self) -> None:
        model = self._mip_model.model
        if model.Status not in {GRB.INFEASIBLE, GRB.INF_OR_UNBD}:
            return

        model.computeIIS()
        model.write("model.ilp")
        raise RuntimeError(f"MIP model infeasible: gurobi status={model.Status}")

    def _build_result(self, problem_data: ProblemData) -> SolveResult:
        model = self._mip_model.model
        if model.SolCount == 0:
            return SolveResult(
                problem_data=problem_data,
                solution=SolutionFactory.build_empty(),
                meta_data=self._build_meta_data(None),
            )

        return SolveResult(
            problem_data=problem_data,
            solution=self._mip_model.extract_solution(problem_data),
            meta_data=self._build_meta_data(model.ObjVal),
        )

    def _build_meta_data(self, objective: float | None) -> dict[str, Any]:
        model = self._mip_model.model

        return {
            "solver_name": self.SOLVER_NAME,
            "status": model.Status,
            "runtime_seconds": model.Runtime,
            "objective": objective,
            "best_bound": model.ObjBound,
            "node_count": model.NodeCount,
        }
