from abc import ABC, abstractmethod

import gurobipy
from gurobipy import GRB

from template.model.data.problem_data import ProblemData
from template.solvers.column_generation.column import Column
from template.solvers.column_generation.duals import Duals


class MasterProblem(ABC):
    """One restricted master over a column pool; a branch and price node builds its own, with its bounds baked into the rows."""

    ARTIFICIAL_TOLERANCE = 1e-6

    @abstractmethod
    def add_columns(self, columns: list[Column]) -> None:
        """Add one variable per column, priced into every row the column covers."""

    @abstractmethod
    def solve_relaxation(self) -> float:
        """Solve the LP relaxation and return its objective."""

    @abstractmethod
    def get_duals(self) -> Duals:
        """Read the row duals the pricer needs."""

    @abstractmethod
    def get_column_values(self) -> dict[Column, float]:
        """Read the last solution's value per column."""

    @abstractmethod
    def get_artificial_usage(self) -> float:
        """Total artificial value in the last solution; anything above the tolerance means the columns cannot cover the rows."""

    @abstractmethod
    def solve_integer(self, time_limit_seconds: float) -> bool:
        """Solve the pool as an integer program and report whether a solution was found."""

    @abstractmethod
    def close(self) -> None:
        """Release the solver resources of this master."""


class SetCoveringMaster(MasterProblem):
    """Every item covered at least once, minimizing the cost of the chosen columns."""

    _problem_data: ProblemData
    _model: gurobipy.Model

    # [item id] -> covering row
    _covering_rows: dict[int, gurobipy.Constr]
    # [item id] -> artificial of that row
    _artificials: dict[int, gurobipy.Var]
    _columns: dict[Column, gurobipy.Var]

    def __init__(
        self, env: gurobipy.Env, problem_data: ProblemData, columns: list[Column]
    ) -> None:
        self._problem_data = problem_data
        self._model = gurobipy.Model(env=env)
        self._model.Params.OutputFlag = 0

        # One artificial costs more than using every resource, so the LP drops them whenever it can.
        penalty = float(len(problem_data.resources) + 1)

        self._covering_rows = {}
        self._artificials = {}
        self._add_covering_rows(penalty)

        self._columns = {}
        self.add_columns(columns)

    def add_columns(self, columns: list[Column]) -> None:
        for column in columns:
            self._columns[column] = self._model.addVar(
                obj=column.cost, column=self._get_column(column)
            )

    def solve_relaxation(self) -> float:
        self._model.optimize()
        assert self._model.Status == GRB.OPTIMAL
        return self._model.ObjVal

    def solve_integer(self, time_limit_seconds: float) -> bool:
        """Binary columns with the artificials closed, so any solution found is a real assignment."""
        for variable in self._columns.values():
            variable.VType = GRB.BINARY
        for variable in self._artificials.values():
            variable.UB = 0.0

        self._model.Params.TimeLimit = time_limit_seconds
        self._model.optimize()
        return self._model.SolCount > 0

    def get_duals(self) -> Duals:
        items = {}
        for item_id, row in self._covering_rows.items():
            items[item_id] = row.Pi
        return Duals(items=items)

    def get_artificial_usage(self) -> float:
        return sum(variable.X for variable in self._artificials.values())

    def get_column_values(self) -> dict[Column, float]:
        return {column: variable.X for column, variable in self._columns.items()}

    def close(self) -> None:
        self._model.dispose()

    def _add_covering_rows(self, penalty: float) -> None:
        for item in self._problem_data.items:
            artificial = self._model.addVar(obj=penalty, name=f"artificial_{item.id}")
            self._artificials[item.id] = artificial
            self._covering_rows[item.id] = self._model.addConstr(
                artificial >= 1.0, name=f"cover_{item.id}"
            )

    def _get_column(self, column: Column) -> gurobipy.Column:
        entries = gurobipy.Column()
        for item_id in column.item_ids:
            entries.addTerms(1.0, self._covering_rows[item_id])
        return entries
