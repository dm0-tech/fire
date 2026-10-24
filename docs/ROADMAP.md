# Attempt 2 roadmap

This roadmap orders questions by dependency. It does not assume that the
project reaches money, or that mechanisms retained from attempt 1 deserve to
return. A phase advances only when its gate is met and its failures are carried
forward.

## Governing question

Can a solvent financial commitment cause self-interested actors to choose
costly actions that causally preserve a specified desirable service?

The first task is to establish the incentive and its real funding. Forecasting,
credit, and money are separate layers. Each must add explanatory or practical
value without hiding the mechanism established below it.

## Economics checklist

Every phase must state:

- actors, information, feasible actions, and objective functions;
- property rights, contract terms, enforcement, and observation rules;
- timing and counterfactual policy;
- numeraire, settlement asset, and units;
- real resource constraints and financial budget constraints;
- stocks versus flows, and assets versus liabilities;
- transfers versus real costs;
- market-clearing and rationing rules;
- participation and incentive-compatibility conditions;
- working capital, financing costs, collateral, and capital constraints;
- rents, risk allocation, loss absorption, default, and bankruptcy;
- the social-welfare criterion and distributional effects;
- the causal comparison and common shocks used to estimate it; and
- assumptions, identification limits, failure conditions, and non-claims.

A new promise is a liability. It is not present labor, equipment, settlement
assets, output, or welfare. Favorable forecasts likewise do not supply real
resources.

## Phase 1: fully funded protection

### Question

Will a self-interested operator choose costly, effective protection when a
beneficiary escrows an outcome-contingent reward?

### Scope

Use the single-service, short-horizon model in `ATTEMPT2_PROMPT.md`. The
treasury holds an outside settlement asset. The action-response curve is known
to a model oracle, effort is initially observable, and no credit or money is
created.

Compare no intervention, fixed maintenance, the protection contract, and the
full-information planner. Reconcile all real and financial accounts. Report
operator rent separately from social surplus.

### Promotion gate

Advance only if:

- the operator's payoff, rather than a prescribed policy, selects effort;
- the analytic and numerical effort choices agree;
- worse baseline conditions induce weakly more effective effort when capacity
  permits;
- common-shock outcomes improve relative to the declared counterfactual;
- the treasury remains solvent under full reward escrow;
- participation, rent, welfare, and working-capital requirements are visible;
- ineffective action, exhausted capacity, and commitment failure remain
  visible as failures; and
- favorable committed-policy forecasts are not mistaken for evidence that
  protection was unnecessary.

Passing means only that one scoped incentive works under restrictive
assumptions.

## Phase 2: forecasting, information, and hidden action

### Question

Can imperfect, heterogeneous forecasters inform the protection decision when
actors anticipate the response and effort or type is not fully observable?

### Additions

- heterogeneous beliefs and information;
- proper forecast scoring and stress-state calibration;
- explicit no-response, named-action, and committed-policy forecasts;
- hidden effort, shirking, and noisy outcomes;
- decision-market or experimental designs where causal identification is
  claimed;
- position limits, manipulation, sabotage, and adverse outside exposure; and
- delayed action and policy feedback.

An ordinary conditional quote does not identify an action's causal effect.
Forecast optimism is not useful effort, and payment for optimistic reports is
not an incentive to improve the world.

### Promotion gate

Advance only if forecast quality is evaluated independently of optimism, the
mechanism handles anticipated intervention explicitly, hidden action cannot
silently replace effective action, and decision quality improves over the
model-oracle or simpler statistical benchmark after market and verification
costs.

## Phase 3: project credit

### Question

Can borrowing move real protective resources forward in time without treating
issuance as income or concealing who bears losses?

### Required transaction

Name:

- the present labor, equipment, or service purchased;
- the seller who accepts the claim or the settlement asset;
- the future revenue, beneficiary commitment, levy, or deliverable that repays
  principal and financing cost;
- the equity, collateral, guarantee, or other capital that absorbs first loss;
- the maturity and liquidity transformation;
- the enforcement and default process; and
- what other use of resources is crowded out.

Compare protection financed from existing assets with debt-financed
protection. Include participation and capital constraints, rollover, default,
bankruptcy, and state-contingent incidence.

### Promotion gate

Advance only if credit increases net protection or welfare over the funded
baseline after financing, default, and crowding-out costs; all balance sheets
reconcile; and no result relies on counting the newly issued liability as a
real resource.

## Phase 4: circulating money

### Question

Can senior payment claims circulate at par while financing or supporting
protection without destroying the incentive, information, or solvency
properties established earlier?

### Required architecture

Keep separate ledgers for:

1. physical service obligations;
2. risky project assets and outcome contracts; and
3. senior liabilities intended to circulate at par.

Explain why holders accept the senior claim, what fixes the unit of account,
what settles redemption, who supplies liquidity, and which capital absorbs
losses before money holders. Model reserve or collateral constraints, maturity
mismatch, market clearing, runs, suspension, default, and bankruptcy. Compare
monetary finance with otherwise identical funded and project-credit cases,
including distributional and price-level effects.

### Promotion gate

The money layer must improve a declared metric after resource, liquidity, and
stability costs; remain solvent under stated stress; preserve the operator's
reason to perform effective protection; and outperform a simpler senior claim
or conventional funding arrangement. Otherwise the research stops at credit
or funded protection.

## Optional hypotheses and re-entry tests

These ideas are not milestones and are not presumed destinations.

### Surprisal

`-log p` may return as a diagnostic or allocation penalty only if it improves a
specified decision over using `p` or `1-p` directly. Any coefficient multiplying
surprisal needs an economic source. Distinguish event probability, expected
fractional delivery, physical belief, and risk-adjusted price.

### Exergy

Exergy may return as a physical input where available work materially improves
the service model. Conservation does not imply that energy in the needed form,
place, and time is economically abundant. Exergy is neither a universal value
measure nor a settlement asset by default.

### Term structure

A term structure may return only after the model contains several genuinely
dated obligations with distinct financing and delivery consequences. Differences
between date-specific success probabilities are not a hazard rate unless the
events are nested survival events.

### Perpetual claims

A perpetual is last. Finite maturities, settlement, rollover, and default must
work first. The perpetual must add measurable persistence exposure rather than
serve as a symbolic requirement.

### Traded forecasts and pricing measures

Start with risk-neutral settlement in one common numeraire. Introduce risk
aversion only with an explicit stochastic discount factor or other priced-risk
model. Separate beliefs, risk premia, liquidity premia, price impact, and
resolution risk before interpreting a quote as physical reliability.

## Research process

For each phase:

1. Write the hypothesis, counterfactual, metrics, and falsification condition.
2. Build the smallest analytic example.
3. Validate the implementation against the analytic result and accounting
   identities.
4. Run predeclared common-shock comparisons and adversarial cases.
5. Record contradictory and null results without parameter shopping.
6. Audit narrative claims against saved outputs.
7. Update decisions and open problems before requesting promotion.

Use independent citation verification. Where practical, withhold predicted
qualitative results from the person or agent running an experiment, and derive
tests from the specification rather than the implementation.

## Archive boundary

Attempt 1 is preserved at tag `attempt1` and branch `attempt1-archive`, both at
commit `8e88597`. Its findings are prior evidence and warnings, not inherited
requirements. The critique of that attempt is `ATTEMPT1_CRITIQUE.md`.
