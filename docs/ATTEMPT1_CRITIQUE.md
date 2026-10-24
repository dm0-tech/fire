# Surprisal money: from confidence-sensitive credit to financed protection

The central idea is worth retaining: make the financial system reward the preservation of explicitly chosen desirable conditions, with forecasts detecting threats before physical failure. My assessment is that `dm0-tech/fire` gets close in its vocabulary and physical accounting, but does not yet implement that incentive mechanism. Its principal implemented loop regulates credit using delivery confidence; the missing loop gives someone a funded, enforceable financial reason to undertake a costly action that improves the desired outcome. This is a conceptual critique and proposed toy-model specification, not a claim that the alternative below solves global public-goods finance.

## What I reviewed

I reviewed the repository at commit `8e88597`, including both source prompts, the model and open-problems documents, the maintenance policies, the issuance engine, the Monte Carlo forecaster, and the liquidity-consol work. The repository describes itself as a toy rather than a proposal, and explicitly acknowledges unestablished repair, strategic-market limitations, risk-premium contamination, and numerical non-convergence ([model](https://github.com/dm0-tech/fire/blob/attempt1/docs/MODEL.md), [open problems](https://github.com/dm0-tech/fire/blob/attempt1/docs/OPEN_PROBLEMS.md)).

I also ran the existing suite: **37 tests passed**. A separate, deliberately narrow 12-period check used identical inflows, a common negative structure shock, 32 forecast paths, and the same seed for the price-target and price-target-plus-repair policies. Its largest absolute treatment differences were:

| Quantity | Maximum absolute difference |
|---|---:|
| Maintenance expenditure | 0 |
| Structure | 0 |
| Food output | 0 |
| Issued face value | 0 |
| Credit ceiling | 0.251662 |

These are my diagnostic results, not a rerun of the repository's full headline ensembles. They illustrate a permitted case in which ceiling relief does not affect real activity; they do not prove that relief can never matter when a ceiling binds.

## The mismatch with the intended idea

Your intended loop, as I understand it, is:

```text
A desirable future becomes less secure
    → the financial reward for effective protection becomes attractive
    → someone finances and performs protection
    → the physical probability of the desirable future improves
    → the financial system can support the resulting commitments.
```

The repository instead gives confidence two monetary roles: higher confidence raises assumed liquidity demand, allowing more issuance at a target price level, while higher surprisal can tighten a credit ceiling. The v2 prompt includes an arrow from issuance to earmarked maintenance, but the engine sets desired maintenance from a configured share of current exergy before searching over issuance; it does not implement purchases of additional maintenance resources with issuance proceeds ([v2 prompt](https://github.com/dm0-tech/fire/blob/attempt1/docs/SURPRISAL_MONEY_PROMPT.v2.md), [engine](https://github.com/dm0-tech/fire/blob/attempt1/sim/engine.py)).

- **The action is prescribed, not incentivized:** the policy code offers constant maintenance, a fixed high-maintenance setting, or a rule that raises maintenance after the ceiling bound. It does not give an economically motivated operator a choice between costly effort, shirking, and manipulation ([policies](https://github.com/dm0-tech/fire/blob/attempt1/sim/policies.py)).
- **“Repair” is not a repair purchase:** the headline repair policy retains constant maintenance and changes the ceiling using lagged delivery forecast errors. That is an experiment in credit relief, not evidence that a private actor finances and performs additional protective work ([policies](https://github.com/dm0-tech/fire/blob/attempt1/sim/policies.py), [engine](https://github.com/dm0-tech/fire/blob/attempt1/sim/engine.py)).
- **Issuance is not net income:** additional promises carry future delivery costs in the physical accounting. Consequently, maximizing the quantity issued is not the same objective as maximizing the issuer's real surplus, much less social welfare ([model](https://github.com/dm0-tech/fire/blob/attempt1/docs/MODEL.md)).

My inference is that adding a better demand curve or a better ceiling cannot, by itself, close this gap. The next model needs an actor's payoff, a choice of real action, and a balance sheet showing who transfers resources to whom.

There is also a potentially procyclical direction to test: if deteriorating forecasts reduce both liquidity demand and permitted credit, they may withdraw financing precisely when protective investment becomes more valuable. That is a proposed stress test, not a result established by my narrow diagnostic.

## Forecasts must include the response they induce

An unconditional market should forecast the outcome under the response people actually expect. Thus a credible promise to intervene can keep the forecast high before the intervention happens; a high forecast is not evidence that intervention is unnecessary. Forecast feedback is a real modeling issue, including the possibility that an optimistic forecast relaxes the response that justified it ([epidemic forecast-feedback analysis](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7416720/)).

Here is a simple derivation, not an empirical model. Suppose success without action has probability \(p_0\), action \(a\) raises that probability locally by \(\alpha a\), and the controller reacts to the final forecast using \(a=k(1-p)\):

\[
p=p_0+\alpha a,\qquad a=k(1-p)
\quad\Longrightarrow\quad
p=\frac{p_0+\alpha k}{1+\alpha k}.
\]

For finite gain and \(p_0<1\), the equilibrium forecast remains below one. With \(p_0=0.6,\alpha=0.2,k=5\), the equilibrium is \(p=0.8,a=1\). At exactly \(p=1\), this response rule supplies no action, so it cannot sustain certainty if continuing action is needed.

This is not an impossibility result for your idea. It suggests a more precise objective: keep the world inside a feasible safety corridor through credible standing commitments, rather than literally peg a market quote to one. Irreversible investment, a continuing maintenance budget, or an outcome contract that remains in force can preserve the action that makes the high forecast rational.

For the toy, distinguish:

- **No-response forecast:** the probability under a specified baseline policy.
- **Action forecast:** the probability if a named, funded action is executed.
- **Committed-policy forecast:** the probability after incorporating the mechanism's actual response.

In a simulator, the first two can be evaluated using common random shocks. In reality, an ordinary conditional market need not identify a causal effect: a decision may reveal hidden information, and the outcomes of unchosen actions remain unobserved. Proper decision markets address incentive problems under particular assumptions, often using randomized decisions and adjusted scoring; merely adding “conditional on action A” markets does not solve these problems ([decision-market analysis](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/DM_full_version.pdf)).

## A price gap is not automatically a repair budget

Suppose an actor acquires \(n\) success claims at price \(p_0\), then performs an action that raises success probability to \(p_1\). In a simplified zero-rate, risk-neutral calculation, its expected trading gain before costs is \(n(p_1-p_0)\). But this expression assumes it can acquire the position at the pre-intervention price; if its intervention is already anticipated, that assumption fails.

This does not imply that trading can never finance useful action. It means that “buy cheap YES, repair the world, sell dear YES” is not yet a mechanism: position acquisition, price impact, capital constraints, competing actors, and anticipated action all need to be specified.

There is also no automatic system-wide alignment. An actor with enough failure exposure could benefit from making failure more likely, and paying people for favorable forecasts could instead reward misreporting. The prediction-mechanism literature explicitly distinguishes truthful information elicitation from avoiding incentives for harmful real-world action; principal alignment can require additional subsidy under the studied assumptions ([Shi, Conitzer, and Guo](https://www.cs.cmu.edu/~conitzer/predictionWINE09.pdf)).

For any proposed currency rule, I would require the following accounting before studying its elegance:

\[
\text{actor's expected payoff}
=\text{real financial receipts}
-\text{action cost}
-\text{financing cost}
-\text{expected liability cost}.
\]

Then compare its chosen action with the action maximizing specified social value net of real costs. A favorable derivative of issuance with respect to confidence is not sufficient.

## Surprisal is useful, but it is not a source of value

For a binary desirable outcome with probability \(p\), the identity
\[
D_{\mathrm{KL}}(\delta_{\mathrm{success}}\Vert P)=-\log p
\]
is a useful way to express distance from certainty. It gives a dimensionless risk coordinate, but it does not determine how much effort society should buy or who will pay for it.

For example, if a reward is \(K\log p\), the coefficient \(K\) supplies the economic scale. Choosing that coefficient, assigning weights to different goals, and deciding which risks are non-compensable are substantive allocation decisions, not consequences of information theory.

I would keep surprisal as a diagnostic and possible allocation penalty, while correcting several distinctions:

- **Fractional delivery is not event probability:** the repository correctly notes that its working \(p=E[\phi]\) is an expected delivered fraction, not the probability of full delivery. A deterministic delivery of 90% gives \(-\log E[\phi]=-\log 0.9\), although the probability of full delivery is zero; this statistic cannot be interpreted as full-delivery reliability ([model](https://github.com/dm0-tech/fire/blob/attempt1/docs/MODEL.md)).
- **Determinism need not mean zero or one:** the prompt and model nevertheless say deterministic fractional delivery produces only zero-or-one forecasts. That conclusion applies to a binary event, not to a known fraction; deterministic \(\phi=0.9\) has expectation 0.9 ([v2 prompt](https://github.com/dm0-tech/fire/blob/attempt1/docs/SURPRISAL_MONEY_PROMPT.v2.md), [model](https://github.com/dm0-tech/fire/blob/attempt1/docs/MODEL.md)).
- **Date-specific success is not survival:** the model calls differences of date-specific delivery surprisal “hazard.” I would reserve that interpretation for nested survival events, since delivery can fail at one date and recover at another ([model definitions](https://github.com/dm0-tech/fire/blob/attempt1/docs/MODEL.md)).
- **A traded quote is not physical reliability:** the repository explicitly models a premium wedge that changes priced surprisal without changing the physical state. The first pedagogical model should assume risk-neutral trading in one common numeraire, then relax that assumption rather than ask one price to identify both risk and beliefs ([model](https://github.com/dm0-tech/fire/blob/attempt1/docs/MODEL.md)).

For multiple goals, \(-\sum_i w_i\log p_i\) can be a declared policy objective, but it is not generally the surprisal of satisfying them jointly. I would give each goal its own failure budget \(1-p_i\leq\epsilon_i\); the union bound then guarantees joint failure probability at most \(\sum_i\epsilon_i\), without assuming independence. This conservative construction is easier to explain than estimating a complete joint tail distribution in the first toy.

## The smaller toy I would build first

I recommend a **funded protection contract**, with money temporarily removed from the mechanism being tested. This is a proposed baseline, not a claim of a new financial instrument.

Use one small power system over a short horizon. Define a success event such as “the system delivers at least \(Q\) units of specified electrical service at the specified connection point during the test window,” with an explicit resource budget. Add an emissions or clean-input condition only after the single-objective loop is legible; the numerical thresholds would be toy assumptions, not engineering estimates.

The actors would be:

- **Beneficiary:** has a declared value \(V\) for successful service and funds a reward.
- **Operator:** can undertake costly maintenance or investment, and chooses effort to maximize its own expected payoff.
- **Forecasters:** estimate outcomes under specified actions and are assessed separately for forecast quality, not optimism.
- **Treasury:** holds outside settlement assets and records funding, liabilities, payments, and defaults.

The irreducible experiment is whether the operator chooses more genuinely effective effort when risk deteriorates, not whether a controller obeys a coded instruction to raise maintenance.

### A solvable first example

Let \(a\) be effort measured in units of the settlement resource, with cost \(c(a)=a\), and let

\[
p(a)=1-(1-p_0)e^{-\kappa a}.
\]

Here \(p_0\) is success probability without the additional effort and \(\kappa>0\) is its effectiveness. A sponsor escrows a fixed reward \(B\), payable to the operator on success; the operator has working capital for effort. Assume risk neutrality, credible settlement, no sabotage or hidden offsetting positions, and a known causal action-response curve for this first experiment.

The operator chooses
\[
\max_{0\leq a\leq A_{\max}}\;B\,p(a)-a.
\]

The solution is
\[
a^*=\min\left\{A_{\max},
\max\left[0,\frac{1}{\kappa}\log\!\big(B\kappa(1-p_0)\big)\right]\right\}.
\]

When the optimum is interior,
\[
p(a^*)=1-\frac{1}{B\kappa}.
\]

The reward does not disappear when the market anticipates success, because it pays for the eventual outcome rather than for moving today's price.

For an illustrative \(B=20,\kappa=1,A_{\max}=4\), my analytic calculation and a numerical grid check give:

| Success without extra effort | Privately chosen effort | Success with effort |
|---|---:|---:|
| 0.90 | 0.6931 | 0.95 |
| 0.60 | 2.0794 | 0.95 |

This is the feedback behavior I would want the first demonstration to show: a worsening underlying condition induces more costly real protection, preserving the chosen reliability level. The committed-policy forecast can remain at 0.95 throughout; the baseline forecast and actual expenditure reveal the threat and response.

If \(B=V\), the operator's marginal effort condition matches the planner's condition for maximizing \(Vp(a)-a\), under these deliberately restrictive assumptions. In this example the incremental social value is approximately 0.3069 in the first row and 4.9206 in the second, but the gross expected reward is 19 in either row. Thus marginal alignment does not imply cost-effective procurement: the contract also pays for baseline success and leaves substantial operator rent.

That limitation should be visible, not hidden. Competition, an entry payment, a performance bond, or a more sophisticated contract could reduce rents, but each introduces participation, collateral, and financing constraints; none should be assumed free. The sponsor must also be able to fund the full promised reward, not just its expected payout.

### What would make it a credible demonstration

Start with the action-response curve known to the simulator and clearly label the first forecast as a model oracle, not a functioning strategic market. Then add heterogeneous forecasters and test whether trading discovers that curve well enough to improve decisions. This sequence separates a working incentive from an assumed forecasting technology.

Compare no intervention, a fixed maintenance budget, the protection contract, and a full-information planner on common shocks. Measure realized service, real effort cost, welfare, treasury solvency, operator profit, and forecast calibration. The price-target gap should not be the headline metric for this experiment.

The most informative failure tests would be:

- **Ineffective repair:** spending is possible but does not improve the physical outcome.
- **Strategic shirking:** announced work is not performed, while observable outcomes remain noisy.
- **Quote manipulation:** an actor can move the market price without changing physical success.
- **Adverse exposure:** an actor can acquire a sufficiently large failure position or profit from delay.
- **Capacity exhaustion:** the target becomes unattainable within the available effort budget.
- **Commitment failure:** expected success rises, the treasury tries to withdraw support, and the original danger returns.
- **Delay:** repair takes time, so an aggressive forecast-driven response can overshoot or arrive too late.

Passing these tests would still establish only a scoped mechanism, not that every actor in the economy is aligned. But it would demonstrate the economic loop more directly than adding another issuance functional to the present model.

## Where exergy and term structure belong

I would retain the physical-resource intuition, but not make a universal exergy currency a prerequisite for testing it. Exergy is defined relative to a reference environment, and the literature itself cautions against turning that engineering measure into a universal measure of resource value or scarcity ([reference-environment analysis](https://www.mdpi.com/1996-1073/5/7/2197)).

The prompt argues that conservation means energy cannot be scarce ([v2 prompt](https://github.com/dm0-tech/fire/blob/attempt1/docs/SURPRISAL_MONEY_PROMPT.v2.md)). That is not a sound economic argument: conservation does not imply availability in the required place, form, or time. My recommendation is to say instead that available work and delivery constraints are often more useful physical inputs for this toy than undifferentiated energy, while leaving valuation separate.

For the first prototype, use explicit service contracts with quantity, location, delivery window, quality, and resource requirements. A dated delivery ladder can then provide a genuine term structure without asserting that a hundred-year promise has the same liquidity or default behavior as a short claim. A perpetual is an interesting later persistence test, not a prerequisite for discovering whether anyone will pay for effective maintenance.

Also keep physical capacity separate from the desirable frontier. More deliverable work need not satisfy an emissions constraint, and a successful energy project need not improve every other goal. When extending to several objectives, require each action package to disclose its effects on the other constraints instead of hiding them in one structure variable.

The liquidity-consol memo should remain a useful balance-sheet warning, not a verdict against the broader idea. It tests a venue-persistence note, rejects native-token-only backing, and regards outside-collateral backing as coherent but not yet an established improvement over familiar claims ([liquidity-consol memo](https://github.com/dm0-tech/fire/blob/attempt1/docs/LIQUIDITY_CONSOL_FALSIFICATION.md)).

## Reintroducing money without losing the mechanism

After the funded protection baseline works, I would add project credit and then circulating payment claims. Keep three ledgers distinct: physical service obligations, risky project assets and outcome contracts, and the senior liabilities intended to circulate at par.

The credit experiment should show exactly how issuing a claim purchases present labor or equipment, which future cash flow or deliverable repays it, which capital absorbs loss, and what limits maturity mismatch. Its meaningful comparison is then protection financed with existing resources versus protection financed by new credit, including crowding out and default.

Potential backing might come from service revenue, explicit beneficiary commitments, enforceable levies, or genuinely monetizable avoided losses. These are design candidates, not resources generated by the forecast itself. Global public goods make identifying and enforcing such payments especially difficult; the toy should expose that boundary rather than rename it seigniorage.

For your broader frontier, define every event with its baseline, observation rule, horizon, controllable actions, and acceptable failure budget. Treat the sea-level, CO2, and inflation bounds as proposed policy conditions requiring separate feasibility and welfare assessment, not as self-validating targets merely because a market can quote them.

## Bottom line

I would preserve the repository as an honest exploration of confidence-sensitive credit, but give the next experiment a different organizing question:

> Can a solvent financial commitment make a self-interested actor choose a costly action that causally preserves a desired future, while forecasts remain informative?

The first milestone is not \(p=1\), a perpetual, or a new monetary standard. It is a small economy where bad news causes economically chosen, funded protection; the resulting outcome improves relative to a specified counterfactual; and neither favorable quotes nor newly issued promises are mistaken for real resources. That would capture the original idea more directly and give a sound base for the integrated financial system you want to explore.
