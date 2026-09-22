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

The direct MIP over Gurobi, split into a solver, a model, and one setter per
formulation part. `MIPSolver` owns everything that is the same in every project: the
solver parameters, the optimize call, the infeasibility handling, and the
`SolveResult`. `MIPModel` owns the Gurobi environment, the Gurobi model, and the
formulation: it builds the variables, hands them to the constraint and objective
setters, and reads variable values back into a `Solution`. The split exists so that a reader can check a single constraint against
the paper without scrolling through the rest of the model, by reading one
`_set_<constraint>` method of the constraint setter, and so that a test can build one
constraint family in isolation and count its rows.

#### Files

- `mip_config.py`: the solver's parameters, a frozen dataclass.
- `mip_variables.py`: `MIPVariables` holds one private container per variable
  family and exposes each family only through a `get_<family>(index)` getter. The
  container type is an implementation detail; nothing outside reads it.
- `mip_constraint_setter.py`: `MIPConstraintSetter.set_constraints` calls one private
  `_set_<constraint>` per formulation constraint. One constraint per method, never
  several grouped into one. Each method builds `lhs` and `rhs` as explicit
  expressions with the same sides as the paper, adds them with
  `model.addConstr(lhs <= rhs, name=...)`, and cites its equation in a one-line
  docstring. Keeping the sides as written makes the code diffable against the
  formulation.
- `mip_objective_setter.py`: `MIPObjectiveSetter.set_objective` builds the objective
  expression and sets the sense.
- `mip_model.py`: `MIPModel` is the abstract formulation. It owns the Gurobi
  environment and the Gurobi model and exposes them as `env` and `model`.
  It takes the constraint setter and the objective setter in its constructor, and
  `build` creates the model and then runs in variables, constraints, objective order,
  keeping the variables for extraction. A subclass owns the two remaining hooks:
  `_build_variables` calls one private `_build_<family>_vars` per decision family and
  returns the `MIPVariables`, and `extract_solution` reads the variable values into a
  `Solution`.
- `mip_solver.py`: `MIPSolver` sets the time limit on the model's environment, starts
  it, has the model build itself, optimizes, raises with an IIS file if the model is
  infeasible, delegates solution extraction to the model, and records the result with
  its meta data. An infeasible model is a bug in the formulation or the instance, so it
  fails loudly with the IIS written next to the run rather than returning an empty
  result.

#### Tests

One test per variable family checking type and bounds, one test per constraint
family checking the row count. Row counts catch the most common formulation slip,
a loop over the wrong index set, without needing a solved instance.

### `solvers/branch_and_price_solver`

A high-level template for column generation inside a branch and bound tree.
The objective is minimized. The template provides the search and pricing loops;
each project supplies its formulation, initialization, feasibility handling,
branching decisions, integrality checks, and solution extraction. The node
selector, the branching rule, the master builder, the pricing builder, the column
generation, the node lower bound generator, the node incumbent generator, and the
solution extractor are all supplied through `BranchAndPriceConfig`, so the solver is
concrete: a project builds `BranchAndPriceSolver(config)` and never subclasses it.
The lower bound generator turns a converged node into the bound
the node is pruned and reported with, and the incumbent generator is the primal
heuristic run on a fractional node. Both receive one `NodeContext`: the node, its live
master, the column generation result, and the incumbent objective so far. A generator
that needs more search state gets a new `NodeContext` field, and existing generators
stay unchanged; project data such as `ProblemData` goes into the generator's
constructor instead.
A project typically plugs in the shipped `RelaxationLowerBoundGenerator`, or its
ceiling when every objective coefficient is integer, and either an integer restricted
master heuristic or the shipped `NoIncumbentGenerator`.

One column pool is shared by the tree. A `BranchNode` holds only its complete
accumulated decisions, `branching_decisions: tuple[BranchingDecision, ...]`, and its
lower bound. The root starts with an empty tuple and a bound of negative infinity.
`BranchingRule.get_children(node, evaluation)` creates the children and reads the
node's relaxation from `evaluation.relaxation_solution`; when branching needs more
data, it becomes a `NodeEvaluation` field filled in `_evaluate_node`, and existing
rules stay unchanged. A rule builds each child as
`BranchNode((*node.branching_decisions, decision), node.lower_bound)`: the new
decision appended to the inherited ones, and the node's bound inherited.

Each project's `BranchingDecision` subclasses carry the branch choice and enforce it
themselves; the builders, the master, the pricer, the column generation, and `Duals`
never inspect a decision. A decision implements three methods:
`is_column_compatible(column)` filters the shared pool, `apply_to_master(master)`
enforces the choice on the node's master once its columns are in, and
`apply_to_pricing(pricing_problem)` enforces it on the node's pricer. The solver
calls the last two once per node, after the builders return and before column
generation starts. `BranchingDecision[M, P]` is generic in the master and pricer
capabilities it needs. Use small `Protocol` interfaces for these capabilities: a
model satisfies the interface by implementing its methods, without inheriting from
it. A decision can bound a column, add a master row, change what may be
priced, or do all of these; a row that only constrains combinations of columns leaves
every individual column compatible.

`MasterProblemBuilder.build(columns)` and `PricingProblemBuilder.build()` are the
project seams: they build the node's master over the compatible columns and the
node's pricer, both with no decision applied. Both models are built fresh for each
node and disposed after use.

Branching implementations belong to the project. Define the model capabilities a
decision needs and extend `Duals` with the data the master and pricer exchange.
The template does not prescribe rows, dual keys, or a particular branching method.
New rules using existing capabilities leave the builders, models, column generation,
and solver unchanged. A rule needing a new capability adds that operation to the
relevant model implementations.

A node already holds multiple decisions. It checks column compatibility against
all of them and applies them to each model in order. A project can put several
restrictions inside its own decision when they describe one branch choice.
The branching rule creates the children that cover the parent's feasible solutions.

#### Combining implementations

`CompositePricingProblem(pricing_problems)` combines a nonempty list of exact
pricing subproblems. Each round calls every subproblem with the same duals, joins
their columns, and removes duplicate keys in first-seen order. It returns no columns
only when all subproblems return none. The subproblems together must cover the node's
whole pricing domain, and each must certify convergence for its own domain. The
composite owns their disposal; each supplied instance must be distinct.

Project-specific capability forwarding is explicit. A project can subclass
`CompositePricingProblem[MyPricingProblem]` and forward its capability methods to
the appropriate items returned by `get_pricing_problems()`. A generic group cannot
decide which subproblem should receive a domain restriction.

To replace a component, implement its interface and supply it through
`BranchAndPriceConfig` or the relevant builder. Simple data such as nodes, duals,
and results stays concrete; projects extend it where needed. No registry or
component-type checks are needed in the search loop. The config uses the core model
interfaces, so it does not statically check optional decision capabilities. Test
each project's configured models with the decisions its branching rules produce.

Open nodes are popped from the configured node selector; best-first, which orders
by the bound inherited from the parent, and depth-first are provided.
Dominated nodes are pruned before building their models. Unknown root bounds
start at negative infinity.

`StandardColumnGeneration` is the shipped loop: it solves the master, prices, adds
fresh columns, and repeats, and never sees a decision; `ColumnGeneration` is the
abstraction a project may replace with a loop of its own. The loop finishes each master
solve and each pricing call on the node's step timer, and reports its rounds and the
columns it added. The pricer must generate
columns compatible with the node's decisions. An empty pricing result certifies
convergence for that node.
The pool only deduplicates; a duplicate-only batch raises because it cannot
establish convergence. After convergence, the master reports whether the node is
feasible. The template does
not prescribe how the master establishes or restores feasibility.

A node is handled in two phases. `_evaluate_node` reads everything the node offers
from its master into a `NodeEvaluation` and changes nothing; the master is then
disposed, and `_settle_node` takes an improving incumbent and decides the outcome from
that data alone, so it is tested without models. The master's `is_integral`, asked
after convergence, decides whether the node supplies the incumbent itself, judged by
its relaxation objective rather than the generator's bound; a fractional node can
still supply one through the incumbent generator, which is only asked there, and a
heuristic incumbent that reaches the node's bound closes the node before it branches.
Extraction runs once
when the search ends, on the incumbent's column values. An exhausted tree
is optimal with an incumbent and infeasible without one. The deadline is checked between nodes, so
the time limit can overrun by one node.

#### Progress logging

```python
config = BranchAndPriceConfig(..., observers=[ProgressLogger()])
```

The solver measures its own steps and reports them as data; observers only format
what they receive. Each node gets a `StepTimer` on the config's `Clock`, and after each
step the solver, or the column generation inside its loop, calls
`finish_step(NodeStep.X)`. A step is charged the time since the previous finished step,
so steps leave no gaps and add up to the node's time, and a step that repeats, such as
the master solve of every round, accumulates. `COLUMN_GENERATION` holds the column
generation time outside master solves and pricing, so a replacement loop that finishes
no steps still has its time in the right column. Adding a timed step takes a
`NodeStep` member and one `finish_step` call; the progress table grows its column
without further changes. The value of a `NodeStep` is its table header.

After each node the observers receive an `ExploredNode`: its id, outcome, compatible
column count, column generation result, child count, `seconds_by_step`, the elapsed
time, and the search bounds. When the search ends they receive a `SearchSummary`,
which the solver also turns into `meta_data`. Observer methods default to doing
nothing, so an observer overrides only the events it needs. Tests run the solver on a
fake clock rather than patching the system time. The design needs only interfaces,
enums, maps, and immutable values, so it carries over to other languages as is.

`ProgressLogger` writes one INFO table row per explored node, with a marker column:
`*` the node was integral and became the incumbent, `H` the incumbent generator
improved it and closed the node, `X` the node was infeasible, blank the node branched
or was pruned. Steps a node never reached print `-`. The summary line is logged when
the search finishes, and at DEBUG each node also gets a per-step block. The logger
keeps no search state, so one instance serves any number of searches. A project that
wants another sink (a progress file, a database, a plot) adds its own
`BranchAndPriceObserver` to `observers`.

A zero incumbent and zero bound show a `0.0%` gap; a zero incumbent with a nonzero
bound shows `inf`, and a missing incumbent shows `-`.

#### Files

- `branch_and_price_config.py`: the search time limit and clock, the node selector,
  the branching rule, the master and pricing builders, the column generation, the
  node lower bound and incumbent generators, the solution extractor, and the
  observers.
- `branch_and_price_solver.py`: the tree loop and the per-node exploration, which
  applies the node's decisions to its models.
- `solution_extractor.py`: turns the incumbent's column values into a `Solution`; an
  empty mapping means no incumbent and yields the empty solution.
- `explored_node.py` and `node_outcome.py`: what one node did, where its time went,
  and how it ended.
- `node_context.py`: what the node generators see about a converged node.
- `node_evaluation.py`: everything read from a node's master before it is disposed.
- `search_summary.py`: how the search ended.
- `branch_and_price_observer.py`: the per-node and end-of-search hooks the solver
  reports to.
- `branching/branch_node.py`: branching decisions and lower bound.
- `branching/branching_decision.py`: the branch choice that filters columns and
  enforces itself on the master and the pricer.
- `branching/branching_rule/branching_rule.py`: the branching hook.
- `branching/node_selector/`: best-first and depth-first node selection.
- `column_generation/column.py` and `column_pool.py`: column identity and storage.
- `column_generation/master/`: the master interface, which also reports the node's
  feasibility and integrality, and `duals.py`, the dual data a project defines.
- `column_generation/master/master_problem_builder.py`: builds a node's master over
  the compatible columns, with no decision applied.
- `column_generation/pricing/`: the pricing interface.
- `column_generation/pricing/composite_pricing_problem.py`: combines pricing
  subproblems and disposes them together.
- `column_generation/pricing/pricing_problem_builder.py`: builds a node's pricer with
  no decision applied.
- `column_generation/column_generation.py`: the solve-price-add interface.
- `column_generation/standard_column_generation.py`: the shipped solve-price-add loop.
- `column_generation/column_generation_status.py` and `column_generation_result.py`:
  convergence status, relaxation objective, round count, and new column count.
- `bounding/`: the node lower bound interface and `RelaxationLowerBoundGenerator`,
  which reports the relaxation objective.
- `incumbent/`: `Incumbent` is an objective with the column values behind it, the
  generator interface, and `NoIncumbentGenerator`, which finds nothing.
- `timing/`: `Clock` and its `SystemClock`, `NodeStep` the timed steps of a node, and
  `StepTimer`, which splits a node's time into those steps.
- `progress/`: the shipped progress logging. `progress_logger.py` is the observer that
  logs a row per node and the summary, and `progress_table.py` renders the header, the
  rows, the per-node debug block, and the summary.

#### Tests

Components scripted through the config (masters, pricers, and trees) test the
generic loops: convergence, deduplication, pruning, incumbent selection, bounds,
infeasibility, and timeouts on a fake clock.
`test_covering_example.py` is a working example with a small covering master and
finite pricing subproblems combined by `CompositePricingProblem`. Its rows and dual
data are defined only in the example, and the builders add the rows to every master
and pricer they build. It checks coefficients for initial and priced columns,
changing row duals, and convergence, with progress logging both enabled and
disabled. Tests start every search from the empty root; decisions are tested on
branched children. It needs no optimization solver license.
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
