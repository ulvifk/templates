from template.solvers.branch_and_price_solver.incumbent.incumbent import Incumbent
from template.solvers.branch_and_price_solver.incumbent.node_incumbent_generator import (
    NodeIncumbentGenerator,
)
from template.solvers.branch_and_price_solver.node_context import NodeContext


class NoIncumbentGenerator(NodeIncumbentGenerator):
    # for projects without a primal heuristic; integral nodes still supply incumbents
    def generate(self, context: NodeContext) -> Incumbent | None:
        return None
