from typing import Any

import gurobipy
from gurobipy import GRB

from template.model.data.problem_data import ProblemData
from template.model.solution.solution import Solution, SolutionFactory
from template.model.solve_result import SolveResult
from template.solvers.mip_solver.mip_config import MIPConfig
from template.solvers.mip_solver.mip_constraint_setter import MIPConstraintSetter
from template.solvers.mip_solver.mip_objective_setter import MIPObjectiveSetter
from template.solvers.mip_solver.mip_variables import (
    MIPVariables,
    MIPVariablesFactory,
)
from template.solvers.solver import Solver


class MIPSolver(Solver):
    SOLVER_NAME = "mip"

    _config: MIPConfig
    _env: gurobipy.Env

    _model: gurobipy.Model
    _variables: MIPVariables

    def __init__(self, config: MIPConfig) -> None:
        self._config = config

        self._configure()

    def solve(self, problem_data: ProblemData) -> SolveResult:
        self._build(problem_data)

        self._model.optimize()
        self._raise_if_model_is_infeasible()

        return self._build_result(problem_data)

    def _configure(self) -> None:
        self._env = gurobipy.Env(empty=True)

        self._env.setParam("TimeLimit", self._config.time_limit_seconds)
        self._env.start()

    def _build(self, problem_data: ProblemData) -> None:
        self._model = gurobipy.Model(env=self._env)

        self._variables = MIPVariablesFactory.build(self._model, problem_data)
        MIPConstraintSetter.set_constraints(self._model, self._variables, problem_data)
        MIPObjectiveSetter.set_objective(self._model, self._variables, problem_data)

    def _raise_if_model_is_infeasible(self) -> None:
        if self._model.Status not in {GRB.INFEASIBLE, GRB.INF_OR_UNBD}:
            return

        self._model.computeIIS()
        self._model.write("model.ilp")
        raise RuntimeError(f"MIP model infeasible: gurobi status={self._model.Status}")

    def _build_result(self, problem_data: ProblemData) -> SolveResult:
        if self._model.SolCount == 0:
            return SolveResult(
                problem_data=problem_data,
                solution=SolutionFactory.build_empty(),
                meta_data=self._build_meta_data(None),
            )

        return SolveResult(
            problem_data=problem_data,
            solution=self._extract_solution(problem_data),
            meta_data=self._build_meta_data(self._model.ObjVal),
        )

    def _build_meta_data(self, objective: float | None) -> dict[str, Any]:
        return {
            "solver_name": self.SOLVER_NAME,
            "status": self._model.Status,
            "runtime_seconds": self._model.Runtime,
            "objective": objective,
            "best_bound": self._model.ObjBound,
            "node_count": self._model.NodeCount,
        }

    def _extract_solution(self, problem_data: ProblemData) -> Solution:
        raise NotImplementedError(
            "Read self._variables values (binary above 0.5, continuous rounded) "
            "into a Solution."
        )
