from template.solvers.branch_and_price_solver.bounding.node_lower_bound_generator import (
    NodeLowerBoundGenerator,
)
from template.solvers.branch_and_price_solver.node_context import NodeContext


class RelaxationLowerBoundGenerator(NodeLowerBoundGenerator):
    def generate(self, context: NodeContext) -> float:
        return context.column_generation_result.relaxation_objective
