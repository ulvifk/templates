# Branch and price

Branch and bound where every node re-solves its LP by column generation. One `ColumnPool` is shared
by the whole tree, so a column generated deep in the tree is available everywhere; the node's own
bounds decide which of the pooled columns its master may use.

## Implement per problem

- `BranchNode` — the bound fields that describe a node completely, plus `root()`. They are aggregate
  bounds, not a decision path, so a master can be built from the node alone.
- `BranchingRule` — how fractional column values become children. `MostFractionalResourceRule` is
  the placeholder stub; an empty child list means the node is integral.
- `BranchPriceSolver._build_master` — a `MasterProblem` that applies the node's bounds.

## Reused as is

The tree loop, `NodeSelector`, pruning, incumbent handling, the time limit, and everything in
`column_generation`.

## How the node bounds flow

node bounds -> extra master rows -> those rows' duals -> the pricer avoids columns the node forbids.
The pricer only ever sees duals, so a bound that is not a master row cannot reach it, and pricing
would keep regenerating forbidden columns.

## Node selection

`NodeSelector` is best first: the heap key is `(lower_bound, insertion counter)`. Depth first is the
same class with the key swapped for the negated depth or the negated counter.
