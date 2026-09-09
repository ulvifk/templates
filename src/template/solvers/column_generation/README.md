# Column generation

Solves the LP relaxation of a set covering formulation whose columns are generated on demand:
the restricted master prices only the columns it holds, the pricing problem answers with columns
of negative reduced cost, and the loop stops when the pricer has nothing left to add.

## Implement per problem

- `Column` — what one column is, and a `key` that identifies it for deduplication.
- `MasterProblem` — the restricted master over the pool. `SetCoveringMaster` is the placeholder:
  one covering row per item, one artificial per row with a big-M cost so the LP is always feasible.
- `PricingProblem` — the separation oracle. `KnapsackPricer` is the placeholder stub.

## Reused as is

`ColumnPool`, `ColumnGeneration`, `ColumnGenerationResult`, `ColumnGenerationSolver`.

## Stopping rule

Deduplication drives termination: the pricer returns candidates, the pool keeps the unseen ones,
and an empty fresh list ends the loop. The pricer therefore never has to prove convergence itself.
Hitting the deadline returns `converged=False`, and that bound must not be used as a node bound.
Artificials left above `MasterProblem.ARTIFICIAL_TOLERANCE` mean no column set can cover the rows,
so the converged bound becomes infinity.
