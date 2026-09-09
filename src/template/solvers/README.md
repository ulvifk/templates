| Package | Formulation | SOLVER_NAME |
| --- | --- | --- |
| `mip_solver` | Direct MIP: binary assignment of items to resources, minimize used resources | `mip` |
| `column_generation` | Set-partitioning master over feasible resource loads, priced by knapsack | `column-generation` |
| `branch_price` | Column generation at every node, branching on the assignment structure | `branch-price` |

Every solver package holds its own config dataclass, exposes `SOLVER_NAME`, and
returns a `SolveResult`. Add one row per package here when a new solver lands.
