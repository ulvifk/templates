# Templates

The structure every optimization-research project here follows. Copy the layout,
rename `template` to the project package, and fill in the seams that raise
`NotImplementedError`. The core modules are always present. The template
packages are copied only when the project needs that technique.

| Template | Path | Use it when |
| --- | --- | --- |
| MIP solver | `src/template/solvers/mip_solver` | The problem is solved directly by a MIP |
| Branch and price | `src/template/solvers/branch_and_price_solver` | Set-partitioning style formulations with a pricing subproblem |
| Local search | `src/template/local_search` | A metaheuristic improves solutions by moves |
| Time-space network | `src/template/time_space_network` | The formulation is a flow over discretized time |

## Core modules

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
returns, and nothing else. `SolutionFactory.build_empty`, in the same file,
returns a solution with every collection empty; solvers report that instead of
`None` when they found no incumbent, so no caller has to guard against `None`.

### `model/solve_result.py`

What a solver hands back: the problem data, the solution (empty when no
incumbent was found), and a `meta_data` dict for solver name, status, runtime,
objective, bound, and whatever else the solver wants to report. Those values
live in one dict rather than typed fields because they differ per solver and
per problem, and nothing downstream branches on them.

### `solvers`

`Solver` is the abstract base every algorithm implements: `solve(problem_data)`
returns a `SolveResult`. Each algorithm lives in its own package under `solvers`
with its own config dataclass.

### `constants.py`

Project-wide constants such as `ZERO_TOLERANCE`. Import them; never redefine them
locally, so every comparison in the project agrees on the same tolerance.

### `logging_config.py`

`configure_logging(level)` takes a `LogLevel` and sets the root logger once, at
the entry point. Modules that log use `logging.getLogger(__name__)` and nothing
else.

## Templates

### `solvers/mip_solver`

The direct MIP over Gurobi, split by responsibility so each file reads like one
part of the formulation. The split exists so that a reader can check a single
constraint against the paper without scrolling through the rest of the model,
and so that a test can build one constraint family in isolation and count its
rows.

#### Files

- `mip_config.py`: the solver's parameters, a frozen dataclass.
- `mip_variables.py`: `MIPVariables` holds one private container per variable
  family and exposes each family only through a `get_<family>(index)` getter.
  `MIPVariablesFactory.build`, in the same file, calls one private
  `_build_<family>_vars` per family and returns the `MIPVariables`. The
  container type is an implementation detail; nothing outside reads it.
- `mip_constraint_setter.py`: `set_constraints` calls one private
  `_set_<constraint>` per formulation constraint. One constraint per method,
  never several grouped into one. Each method builds `lhs` and `rhs` as explicit
  expressions with the same sides as the paper, adds them with
  `model.addConstr(lhs <= rhs, name=...)`, and cites its equation in a one-line
  docstring. Keeping the sides as written makes the code diffable against the
  formulation.
- `mip_objective_setter.py`: `set_objective` builds the objective expression and
  sets the sense.
- `mip_solver.py`: `MIPSolver` configures the environment, builds the model in
  variables, constraints, objective order, optimizes, raises with an IIS file if
  the model is infeasible, and extracts the `Solution` from variable values. An
  infeasible model is a bug in the formulation or the instance, so it fails loudly
  with the IIS written next to the run rather than returning an empty result.

#### Tests

One test per variable family checking type and bounds, one test per constraint
family checking the row count. Row counts catch the most common formulation slip,
a loop over the wrong index set, without needing a solved instance.

### `solvers/branch_and_price_solver`

A high-level template for column generation inside a branch and bound tree.
The objective is minimized. The template provides the search and pricing loops;
each project supplies its formulation, initialization, feasibility handling,
branching decisions, integrality checks, and solution extraction. The node
selector, the branching rule, the master builder, the pricing builder, and the
column generation are all supplied through `BranchAndPriceConfig`; the solver keeps
`_extract_solution` as its one abstract method.

One column pool is shared by the tree. Each node stores its complete accumulated
decisions in `branching_decisions: tuple[BranchingDecision, ...]`.
The root starts with an empty tuple. `BranchingRule.get_children(node)` creates
the children. Its `_build_child(node, decision)` helper appends the new
decision to the inherited ones, retains the parent's lower bound, and clears
the relaxation solution.

Each project's `BranchingDecision` subclasses carry the branch choice and implement
`is_column_compatible(column)`. The solver filters the shared pool against every
decision on the node's path and passes the result to
`MasterProblemBuilder.build(node, columns)`. That builder includes all supplied
columns and applies the decisions to the master. `PricingProblemBuilder.build(node)`
applies the same decisions to the pricing formulation and reduced-cost
calculation. A decision can add a master row, change the pricing structure, or do
both; it need not represent a variable bound. A master row that only constrains
combinations of columns can leave every individual column compatible. Both models
are built fresh for each node and disposed after use.

Open nodes are popped from the configured node selector; best-first, which orders
by the bound inherited from the parent, and depth-first are provided.
Dominated nodes are pruned before building their models. Unknown root bounds
start at negative infinity.

`StandardColumnGeneration` is the shipped loop: it solves the master, prices, adds
fresh columns, and repeats; `ColumnGeneration` is the abstraction a project may
replace with a loop of its own. The pricer must generate columns compatible with
the node's decisions. An empty pricing result certifies convergence for that node.
The pool only deduplicates; a duplicate-only batch raises because it cannot
establish convergence. After convergence, the master reports whether the node is
feasible. The template does
not prescribe how the master establishes or restores feasibility.

The master's `is_integral`, asked after convergence, decides which node supplies
the incumbent, and extraction runs once when the search ends. An exhausted tree
is optimal with an incumbent and infeasible without one. The deadline is checked between nodes, so
the time limit can overrun by one node.

#### Files

- `branch_and_price_config.py`: the search time limit, the node selector, the
  branching rule, the master and pricing builders, and the column generation.
- `branch_and_price_solver.py`: the tree loop and the solution extraction hook.
- `branching/branch_node.py`: branching decisions, relaxation bound and
  `master_relaxation_solution`, and the root factory.
- `branching/branching_decision.py`: branch choice data and column compatibility.
- `branching/branching_rule/branching_rule.py`: the branching hook and child construction.
- `branching/node_selector/`: best-first and depth-first node selection.
- `column_generation/column.py` and `column_pool.py`: column identity and storage.
- `column_generation/master/`: the master interface, which also reports the node's
  feasibility and integrality, and the dual data placeholder.
- `column_generation/master/master_problem_builder.py`: builds a node's master from
  the compatible columns and the node's decisions.
- `column_generation/pricing/`: the pricing interface.
- `column_generation/pricing/pricing_problem_builder.py`: builds a node's pricer with
  the same decisions applied.
- `column_generation/column_generation.py`: the solve-price-add interface.
- `column_generation/standard_column_generation.py`: the shipped solve-price-add loop.
- `column_generation/column_generation_status.py` and `column_generation_result.py`:
  convergence status, bound, and round count.

#### Tests

Components scripted through the config (masters, pricers, and trees) test the
generic loops: convergence, deduplication, pruning, incumbent selection, bounds,
infeasibility, and timeouts.
Formulation and pricing tests belong in the project built from this template.

### `local_search`

The building blocks a local search is assembled from. This package is not a
solver and holds no search loop: a metaheuristic solver package (GRASP, ILS,
VND, ...) builds its construction, perturbation, and loop on top of these
pieces and lives under `solvers`.

#### Files

- `move.py`: `Move` is one candidate change to a solution. It reports
  feasibility, a memoized gain (positive means better), and `apply`, which
  returns a new `Solution`. The gain is memoized because feasibility and
  acceptance both need it and computing it is the expensive part of a scan.
- `move_generator.py`: `MoveGenerator.for_each_move` builds the moves of one
  move type one at a time and hands each to a `MoveConsumer`. It returns as soon
  as the consumer answers that it has seen enough. This push design is the point
  of the package: a first-improvement scan stops at the first improving move, and
  a generator that built the full list first would enumerate every move it will
  never look at. Never build the full list. One generator per move type, named
  after it.
- `move_consumer.py`: the acceptance rule, separated from enumeration so the same
  generator serves both strategies. `BestMoveConsumer` scans everything and
  keeps the best gain above `ZERO_TOLERANCE`; `FirstMoveConsumer` stops the
  scan at the first improving move.
- `neighborhood.py`: `Neighborhood.improve` composes a generator with a consumer
  and returns the improved solution, or the very same object when nothing
  improves. Callers detect "no improvement" by identity, so no flag or wrapper
  type is needed.

#### Tests

Consumers and neighborhoods are tested with fake moves and generators. Each real
generator gets a test on the moves it enumerates and the order it enumerates
them in, because enumeration order decides what first improvement finds.

### `time_space_network`

How a discretized time-space network is represented and constructed. The
package builds the network only; the MIP over it follows the `mip_solver`
template, with one variable per arc and flow conservation per node.

A node is a location at a time step. A column is the time axis of one location.
Source and sink are timeless and bracket every path. Arcs are typed by subclass
rather than by an enum field, so constraints and extraction select arcs with
`isinstance` and a new arc type is a new class, not a new branch in every switch.

#### Files

`data/` is the frozen result and `constructor/` is the machinery that builds it,
so nothing that reads a finished network ever imports a builder.

- `data/time_space_network_config.py`: the discretization step.
- `data/ts_node/`: `TSNode`, the timeless `TSSourceNode` and `TSSinkNode`, and
  `TSNetworkNode` with `location_id` and `time_minute`, one class per file. Add
  one subclass per location role, carrying the ids that role needs.
- `data/ts_arc/`: `TSArc` with tail, head, and cost, plus `GroundArc`, the one
  arc type every network has. Add one subclass per arc type.
- `data/ts_column.py` and `data/ts_network.py`: `TSNetwork` holds the columns by
  location, the arcs by id, and outgoing and incoming arcs by node, because flow
  conservation reads both directions and should never rebuild them.
- `constructor/discretization.py`: `ceil_to_step` and `floor_to_step`, the only
  two ways a continuous minute becomes a grid minute. Every rounding in the
  project goes through them so the grid is consistent.
- `constructor/ts_column_builder.py` and `constructor/ts_network_builder.py`:
  the mutable side. `TSNetworkBuilder` allocates ids, creates a node once per
  location and time, and turns everything into a `TSNetwork` at the end.
  `_create_node` is per problem: it maps a location to the node subclass for its
  role.
- `constructor/feasible_arc_calculator.py`: per problem. Given a tail node,
  return every arc that may leave it, creating head nodes through the builder as
  needed. Dispatch on the tail node's type, one private method per arc type.
- `constructor/forward_expansion.py`: grows the network from the source by
  asking the calculator for the feasible arcs of every reached node, until
  nothing new is reached. Only reachable nodes ever exist, which keeps the
  network small.
- `constructor/backward_prune.py`: one depth-first pass backward from the sink,
  recording every node and arc it touches; everything untouched is deleted.
  Forward expansion creates dead ends whenever a feasible arc leads somewhere no
  further arc is feasible, and a dead end is a variable the MIP can never use.
- `constructor/time_space_network_constructor.py`: forward expansion, backward
  prune, build.

#### Tests

The builder, the prune, and the expansion are tested on tiny hand-built networks
with fake nodes and a scripted calculator. Each real calculator gets a test per
arc type on the arcs it emits from a given tail.

## Conventions that apply everywhere

- Factories are a separate class in the same file as the class they create,
  never static methods on that class.
- Containers of solver objects (variables, nodes, arcs) are explicit dicts,
  lists, or nested lists, indexed by ids, with a `[key] -> value` comment. They
  are private and reached only through named getters.
- Tests mirror `src` package by package and test real logic only; a stub that
  raises has no test.
