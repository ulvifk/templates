# Templates

The structure every optimization-research project here follows. Copy the layout,
rename `template` to the project package, and fill in the seams that raise
`NotImplementedError`.

## Modules

### `validation`

Validates a `ProblemData` instance before anything runs on it. One class per rule,
each raising on the first violation, and a `Validation` facade that runs every
registered rule in order.

This is the place to let AI agents go wide. What exactly a rule checks matters
little, because a false positive is cheap and a false negative is not: a rule that
fires wrongly costs a minute of reading the message, while a bad instance that slips
through costs a wrong result nobody notices. So even a buggy rule is useful. It warns,
we look, we fix either the rule or the data. Write many rules, write them strictly,
and do not spend time debating whether one is redundant.

### `feasibility`

The same idea applied to a `Solution`. One class per check, each raising on the
first violation, and a `FeasibilityValidation` facade that runs every registered
check against the solution and the instance it claims to solve.

Together, validation and feasibility are the extensive checks that ensure the
instance we solved and the solution we report belong to each other. Every solver
result passes through them before it is trusted.

### `model/data`

The input side. `ProblemData` is a frozen dataclass holding one tuple per entity,
tuple index equal to the entity id. Everything about an instance is stored in it,
and it is the single access point for that data: solvers, rules, and checks read
from `ProblemData` rather than carrying their own copies or lookups. Keep it
idiomatic: plain dataclasses and tuples, no wrapper classes around them.
`ProblemDataParser` reads and writes the JSON form of an instance.

### `model/solution`

The output side. `Solution` is a frozen dataclass holding the decisions a solver
returns, and nothing else.

### `model/solve_result.py`

What a solver hands back: the problem data, the solution (or `None` when no
incumbent was found), and a `meta_data` dict for solver name, status, runtime,
objective, bound, and whatever else the solver wants to report.

### `solvers`

`Solver` is the abstract base every algorithm implements: `solve(problem_data)`
returns a `SolveResult`. Each algorithm lives in its own package under `solvers`
with its own config dataclass.

### `constants.py`

Project-wide constants such as `ZERO_TOLERANCE`. Import them; never redefine them
locally.

### `logging_config.py`

`configure_logging(level)` takes a `LogLevel` and sets the root logger once, at
the entry point. Modules that log use `logging.getLogger(__name__)` and nothing
else.
