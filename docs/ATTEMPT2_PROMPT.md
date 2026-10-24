# Prompt: build the funded-protection baseline

You are building the second attempt at this research repository. Read this
document, `ROADMAP.md`, and `ATTEMPT1_CRITIQUE.md` before writing code.

The organizing question is:

> Can a solvent, pre-funded commitment make a self-interested actor choose a
> costly action that causally preserves a specified desirable service?

The first attempt began with a monetary mechanism. It regulated credit using
delivery confidence but did not give an actor a funded reason to buy or perform
additional protection. Attempt 2 starts with that missing loop. Phase 1 contains
no money creation, credit issuance, price-level target, liquidity-demand
function, surprisal ceiling, exergy numeraire, term structure, or perpetual.

This is a toy mechanism and not a financial or monetary proposal. Do not invent
empirical parameters, institutional endorsements, or evidence. Label numerical
values as toy assumptions and conjectures as conjectures.

## 1. Required deliverables

Build:

1. `README.md`: a short statement of the question, mechanism, assumptions,
   findings, and non-claims.
2. `docs/MODEL.md`: actors, timing, equations, accounting identities, forecast
   semantics, and welfare criterion.
3. `docs/DECISIONS.md`: choices made where this prompt is silent.
4. `docs/OPEN_PROBLEMS.md`: unresolved issues graded as headline or serious.
5. `sim/`: a deterministic analytic check and reproducible stochastic
   experiments with tests.

Keep model code free of file I/O. Put runners and output writing at the edge.
Use the simplest language and dependency set that supports transparent
numerical work.

## 2. Define the service before the instrument

Use one small power-service example over a short horizon. Define success in
terms of:

- quantity of electrical service;
- connection point or location;
- delivery window;
- quality and tolerance;
- observation and resolution rule;
- baseline policy and initial physical state;
- controllable protective action;
- real resource and action-capacity limits; and
- acceptable failure probability.

The thresholds are toy assumptions, not engineering estimates. Begin with one
objective. Do not add emissions, cleanliness, or multiple social goals until
the one-objective mechanism is legible.

Success must be a binary event in the first model. If fractional service is
later reported, keep expected delivered fraction separate from the probability
of meeting the success threshold.

## 3. Actors, rights, and timing

Model four roles:

- **Beneficiary:** values successful service at `V` units of an outside
  settlement asset and funds the promised reward.
- **Operator:** has working capital, chooses costly effort, receives the reward
  on success, and maximizes its own expected payoff.
- **Treasury:** escrows outside settlement assets, records assets and
  liabilities, settles the contract, and reports any default.
- **Forecast oracle:** initially knows the action-response law used by the
  simulator. It is a benchmark, not a strategic prediction market.

Use this timing:

1. The baseline state and contract terms are public.
2. The beneficiary deposits the full maximum reward with the treasury.
3. The operator accepts or rejects the contract.
4. The operator chooses and pays for effort.
5. The physical shock occurs and service is observed.
6. The treasury pays the reward on success and closes the contract.

State ownership, enforcement, observability, and the operator's outside option.
The initial baseline assumes effort is observable and enforceable, no sabotage,
no hidden offsetting position, risk neutrality, and credible settlement. These
are assumptions to relax, not properties established by the run.

## 4. Solvable first model

Let:

- `p0 ∈ (0,1)` be success probability without additional effort;
- `a ∈ [0,A_max]` be real protective effort;
- `c(a) = a` be effort cost in settlement-resource units;
- `κ > 0` be action effectiveness; and
- `B ≥ 0` be the fully escrowed reward paid to the operator on success.

Use:

```text
p(a) = 1 - (1 - p0) exp(-κa).
```

The operator solves:

```text
max over 0 ≤ a ≤ A_max of B p(a) - a.
```

Its optimum is:

```text
a* = min(A_max, max(0, log(Bκ(1-p0)) / κ)).
```

At an interior optimum:

```text
p(a*) = 1 - 1/(Bκ).
```

Validate this expression with a numerical optimizer or grid before introducing
stochastic dynamics. Include boundary cases where effort is zero and where the
capacity limit binds.

The full-information planner solves:

```text
max over 0 ≤ a ≤ A_max of V p(a) - a.
```

Compare the private and planner choices. When `B = V`, their marginal
conditions agree under the baseline assumptions, but the gross success payment
also rewards baseline success and may leave substantial operator rent. Report
that rent; do not equate marginal alignment with cost-effective procurement.

## 5. Accounting requirements

Promises are liabilities, not resources. Issuance, forecasts, or favorable
prices never enter a resource constraint as income.

For every run, reconcile:

- beneficiary funding and residual value;
- treasury cash, escrow liability, payment, refund, and default;
- operator receipts, effort cost, financing cost, expected liability cost,
  profit, and working-capital requirement;
- real resource use, distinct from financial transfers; and
- social value, real cost, and net welfare.

At minimum, show:

```text
operator expected payoff
  = expected financial receipts
  - action cost
  - financing cost
  - expected liability cost
```

and:

```text
social surplus
  = V × realized success
  - real action cost
  - other real resource costs.
```

Do not subtract a transfer from social welfare twice. The treasury must escrow
the full promised reward, not merely its expected payout. A contract that
cannot settle in the failure or success states it promises is insolvent and
must be reported as such.

## 6. Forecast semantics and causal comparisons

Keep these objects separate:

- **No-response forecast:** success probability under the stated baseline
  policy.
- **Action forecast:** success probability if a named action is executed.
- **Committed-policy forecast:** success probability after incorporating the
  mechanism's actual response.

A credible response can keep the committed-policy forecast high even when the
no-response forecast deteriorates. A high final forecast is therefore not
evidence that effort was unnecessary.

In the simulator, estimate counterfactual differences using common random
shocks. The oracle may read current state, model parameters, and named actions;
it may not read future realized shocks. Do not claim that an ordinary
conditional market identifies causal effects. Strategic forecasting belongs
to a later phase.

## 7. Required comparisons

On identical shock paths compare:

1. no additional intervention;
2. a fixed maintenance budget;
3. the funded protection contract; and
4. the full-information planner.

Report distributions or intervals, not a selected run, for:

- realized service and success frequency;
- effective effort and real effort cost;
- no-response, action, and committed-policy forecasts;
- operator profit and rent;
- beneficiary payoff;
- treasury assets, liabilities, payments, and defaults;
- social surplus; and
- the gap between private and planner effort.

The headline question is whether a self-interested operator chooses more
genuinely effective effort when the baseline worsens, subject to capacity, and
whether that effort improves outcomes on common shocks. A coded controller
being instructed to raise maintenance does not answer the question.

## 8. Required failure and sensitivity tests

Implement the cheapest clear version of each:

- **Ineffective action:** spending does not improve success probability.
- **Strategic shirking:** promised effort is not performed while outcomes
  remain noisy.
- **Quote manipulation:** a reported forecast can move without physical
  improvement.
- **Adverse exposure:** the operator can benefit from failure or delay.
- **Capacity exhaustion:** the desired reliability is infeasible within
  `A_max`.
- **Commitment failure:** expected success rises and the sponsor attempts to
  withdraw the support that made it rational.
- **Delay:** effort affects success only after a lag.
- **Funding and participation stress:** the sponsor cannot fully escrow the
  reward or the operator lacks working capital.

Failure must remain visible. Do not tune parameters until a preferred story
returns. State in advance what result would refute the scoped mechanism.

## 9. Phase-1 acceptance gate

Phase 1 passes only if:

- the full maximum reward is escrowed in an outside settlement asset;
- every transfer, stock, liability, and real resource use reconciles;
- the operator chooses effort from its payoff rather than following a
  prescribed maintenance rule;
- numerical effort matches the analytic optimum in the solvable case;
- worsening baseline conditions induce weakly greater effective effort when
  capacity permits;
- common-shock comparisons identify the contract's causal improvement over no
  intervention and fixed maintenance;
- welfare, operator rent, treasury solvency, and failures are separate metrics;
- forecast labels distinguish baseline, action, and committed policy;
- ineffective action and capacity exhaustion fail visibly; and
- the repository can be run and tested from a clean checkout.

Passing this gate establishes only a scoped funded-protection incentive. It
does not establish a prediction market, a credit system, or money.

## 10. Research discipline

- Write hypotheses and failure thresholds before running experiments.
- Prefer the cheapest countermodel to confirmatory complexity.
- Use common random numbers and report intervals across predeclared seeds.
- Do not choose the best-looking seed or retune after seeing the result.
- Write tests from the specification and accounting identities, not from
  implementation details.
- Separate citation verification from prose drafting. Cite only sources that
  were checked to exist and support the attributed claim.
- Keep notation owned and consistent across code and documentation.
- Audit the final narrative against saved results. Preserve contradictions.
- Record consequential choices and keep unresolved problems visible.

Read `ROADMAP.md` before proposing any extension. No later mechanism may be
added merely because it appeared in attempt 1.
