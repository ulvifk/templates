# Templates

Code skeletons that define how optimization-research projects are structured here.
They are a reference to hand to a coding agent, not a runnable project: domain
logic that depends on a concrete problem raises `NotImplementedError`, while the
algorithmic plumbing (parsing, validation, benchmarking, solver wiring) is real
code. The placeholder domain is bin packing: `Item`s with a weight assigned to
`Resource`s with a capacity, minimizing the number of used resources.

## Index

| Template | Path | What it gives you |
| --- | --- | --- |
| Project structure | `src/template` | Data model, solution model, validation, feasibility, entry scripts, tests |
| MIP solver | `src/template/solvers/mip_solver` | Gurobi model split into variables / constraints / objective setters |
| Column generation | `src/template/solvers/column_generation` | Master problem, pricing loop, column store |
| Branch and price | `src/template/solvers/branch_price` | Branching tree on top of column generation |

Conventions live in `AGENTS.md`. Each solver package has its own README describing
its formulation; `src/template/solvers/README.md` indexes them.

## How to use

Hand an agent this repository plus a filled-in version of the prompt below.

```
Initialize a new project at <path> from /Users/ulvifk/git-repo/templates.
Read README.md, AGENTS.md and the README of each solver package you need.
Package name: <x>.
Problem: <...>.
Entities: <...>.
Solution: <...>.
Objective: <...>.
Solvers: <...>.
Design factors: <...>.
Done means all four checks green, generate_data.py writes the grid,
main.py solves one instance.
```

The four checks are `uv run ruff check .`, `uv run ruff format .`,
`uv run pyrefly check`, and `uv run pytest`.
