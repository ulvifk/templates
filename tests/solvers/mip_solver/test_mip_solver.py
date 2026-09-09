from template.feasibility.feasibility_validation import FeasibilityValidation
from template.model.data.problem_data import ProblemData
from template.model.solve_status import SolveStatus
from template.solvers.mip_solver.mip_config import MIPConfig
from template.solvers.mip_solver.mip_solver import MIPSolver


def test_mip_solver_finds_known_optimum(valid_problem_data: ProblemData) -> None:
    solver = MIPSolver(MIPConfig(time_limit_seconds=60.0))

    result = solver.solve(valid_problem_data)

    assert result.status is SolveStatus.OPTIMAL
    assert result.objective_value == 2.0
    FeasibilityValidation.validate(result.solution, valid_problem_data)
