# Liquidity consol: falsification memo

Status: **decision memo, not a proposal**. Checked 2026-10-14.

## Decision

**Verdict: dominated but reusable.**

The strong native-collateral construction fails the first gate. A venue token is
not independent backing for a liability whose bad state is failure of that same
venue. Consolidation removes the apparent asset: when venue health falls, both
the note's earning mechanism and its redemption asset fall together. Issuing
more notes can add outside assets, but issuing notes to buy or support the
venue token does not.

An externally collateralised construction is coherent, but it is not yet a new
kind of credit. It is a restricted market-maker or default-fund claim with a
venue-persistence covenant. That narrower object could be useful. The novel
claim would have to be that coupling the claim to a dated credit-information
venue produces *more reliable stressed-state depth per outside dollar* than a
reserve, LP share, default-fund bond, or direct liquidity subsidy. Neither the
existing model nor the probes below establish that.

The fastest reason not to build a venue is therefore not “prediction markets do
not work.” It is more elementary:

1. native collateral supplies no independent recovery resource;
2. fixed-spread depth is an adverse-selection subsidy, not neutral maintenance;
3. the externally backed payoff is already replicable with familiar claims; and
4. a market price is not a physical default or recovery probability.

## 1. Instrument being tested

This memo tests a **venue note**, not a note issued by the sovereign, processor,
or payment corridor being forecast.

Let:

- `N(T, X)` be one note maturing at `T`, associated with a standardized market
  on external subject `X`;
- `C` be the settlement collateral accepted by that market;
- `V` be a venue/governance token;
- `A_T` be segregated assets available to noteholders at `T`;
- `L_T` be note face outstanding;
- `E_T`, `D_T`, and `O_T` indicate that the market exists, has committed
  executable depth, and reaches a valid resolution;
- `G_T = E_T D_T O_T`; and
- `w_T = min(1, A_T / L_T)` be balance-sheet recovery.

The thesis-faithful payoff is

```
R_T = G_T · w_T units of C credited as usable collateral in market (T, X).
```

That payoff must be distinguished from a safer wind-down claim:

```
R'_T = G_T · w_T collateral-in-market + (1 − G_T) · w_T cash recovery.
```

`R_T` is a catastrophe-style persistence bet: collateral is deliberately lost
when the venue fails even if segregated assets remain. `R'_T` is ordinary
secured debt plus a service covenant. The fallback that makes the instrument
safe also weakens the claim that the deliverable is market persistence. This is
not a drafting detail; it is the first product fork.

“Full recovery of sovereign bond value” should not be encoded as a binary
default contract when actual recovery is fractional. A suitable subject market
quotes either a scalar recovery distribution or a ladder of threshold claims.
A payment corridor is a joint event: both endpoints, settlement finality, and
the legal route must work. A processor is a portfolio of correlated merchant,
bank, network, fraud, and operational risks.

## 2. Four objects that must not be collapsed

1. **The note** is the venue's liability and possible unit of account.
2. **Settlement collateral `C`** is what pays traders and noteholders.
3. **Venue token `V`** may govern, absorb losses, or represent the note.
4. **Event contracts** pay according to external credit or operational events.

Representing the note as a token is technically harmless. Denominating it in
`V` adds basis risk. Redeeming it only in `V` creates wrong-way collateral risk.
Calling all three “the token” hides rather than resolves that distinction.

## 3. State machine

### Issue

An investor contributes outside collateral `C`. The venue mints `N`. The
contract fixes how much enters:

- a bankruptcy-remote redemption reserve;
- a market-making endowment;
- oracle and dispute bonds; and
- operating expenditure.

No claim of backing may count the venue's own note as an asset after
consolidation.

### Maintain

The endowment posts executable orders under a public rule: maximum spread,
minimum size, minimum uptime, inventory limit, cancellation latency, and
stress-state obligation. Fees and explicit subsidies accrue to the endowment.
Informed traders and stale quotes impose losses. “Depth” means executable size
after cancellation and self-trade filters, not displayed orders or volume.

### Resolve

The event contract follows a rule fixed before trading. Proposal and dispute
bonds are separate from market-making inventory. A resolution process can be
well funded while the book is thin, or the book can be deep while the oracle is
captured; `D_T` and `O_T` are separate tests.

### Redeem

At `T`, the holder receives the contracted market-collateral position if
`G_T = 1`. If `G_T = 0`, the contract must choose explicitly between zero,
fractional wind-down recovery, or extension to a replacement venue. Silence
would let governance choose the state after observing who wins.

### Impair and wind down

Maker losses, oracle losses, operating costs, and note redemptions reduce
assets. Withdrawal rules must be mechanical. If the endowment may leave just
before stress, calm-state depth is not maintenance. If it may not leave, the
note is junior capital and should be described and priced as such.

## 4. Consolidated balance sheet

At any time:

```
A = C_reserve + C_market_maker + outside_receivables + marked_value(V_reserve)
L = notes + trader_payables + oracle_payables + senior_operating_claims
equity = A − L
```

Cash conservation over a period requires:

```
outside note proceeds + trading fees + outside subsidy
= reserve increase + maker-capital increase
  + informed-flow loss + oracle loss + operating cost + redemption.
```

Self-trades between the venue, issuer, maker, and treasury vanish on
consolidation. A higher quoted price created by those trades is not an asset.
Buying `V` with note proceeds changes the label on assets but does not introduce
an outside loss bearer.

Five states expose the construction:

- **Healthy:** fees may offset some maker loss; both collateral versions pay.
- **Information shock:** stale two-sided quotes transfer value to informed
  traders. Depth is consumed precisely when it is informative.
- **Run:** notes and `V` sell together; `V` cannot hedge note redemption.
- **Oracle dispute:** dispute capital is encumbered while maker inventory and
  note liabilities remain.
- **Common credit shock:** several subject markets become one-sided together.
  Marginal default probabilities understate the joint drain.

## 5. Fatal-flaw gates

### Gate 1 — accounting and circularity

**Native-token redemption: failed.** If `V` is the principal reserve, the same
state that impairs the venue impairs backing. New note demand can postpone the
shortfall but cannot make `V` an external asset. This is economic circularity,
even though “the market survives” and “the market forecasts survival” are
logically different propositions.

**Externally collateralised redemption: passed narrowly.** Outside collateral,
segregated from operations and enforceable in wind-down, makes the liability
well defined. It also turns the venue token into governance/equity rather than
money-like backing.

Kill rule applied: no native-token-only prototype. A token representation may
survive only if redemption is a fixed claim on segregated outside assets.

### Gate 2 — replication and usefulness

The surviving payoff can be assembled from existing forms:

- a reserve share supplies pro-rata collateral recovery;
- an LP or market-maker share supplies fee income and inventory loss;
- a default-fund contribution supplies mutualised venue-loss exposure;
- venue debt or equity supplies persistence exposure;
- a catastrophe bond supplies a zero-or-impaired payoff on venue failure;
- CDS and digital default swaps isolate default; recovery swaps isolate
  realized recovery.

**Result: failed as a claim of a new primitive; passed as a packaging
experiment.** The note needs a measured advantage over this replication set.
The useful candidate is a transparent junior funding claim whose proceeds are
restricted to dated market depth and dispute security. That is closer to a
market-maker bond than a new currency.

### Gate 3 — neutral-depth incentives

A symmetric quoting rule can separate *eligible orders* from explicit
directional buys, but cannot make market making economically neutral:

- a filled maker ends with inventory;
- stale quotes are selected by better-informed flow;
- cancellation rights make displayed depth disappear in stress;
- no-cancellation commitments make the endowment absorb the stress;
- wash flow can manufacture volume but not outside risk-bearing capacity; and
- the issuer can influence midpoint, market selection, spread parameters,
  reward weights, and resolution language without placing an obvious one-sided
  trade.

Polymarket's current reward rules are useful evidence of what can be enforced:
minimum size, maximum spread, sampled orders, and a boost for two-sided depth.
They are not proof of neutrality; single-sided orders can still score in the
interior probability range. The venue's current UMA path separately uses
proposal and dispute bonds. This separation is evidence against collapsing
liquidity and resolution into one undifferentiated “maintenance” budget.

**Result: the strong collapse claim failed.** Market-making capital is
maintenance in the limited sense that it buys executable access. It is also a
subsidy to informed price discovery and may not fund resolution integrity.
Those functions can share a treasury, but they are not one mechanism.

### Gate 4 — price interpretation

The raw event price combines physical expected loss or recovery, risk premium,
liquidity premium, collateral basis, and resolution risk. Sovereign CDS
practice has the same problem: default intensity and loss given default are not
read from a spread without assumptions, and market-implied estimates live under
a pricing measure.

The repository's E5 already holds physical state fixed while changing only the
premium wedge: B3 first binds at `theta = 0.5`, while liquidity service falls
from about `0.96` to `0.012`. A controller that calls the raw quote a default
probability therefore fails before any venue-specific complication.

**Result: failed for raw-price control; unresolved for an estimator using an
independent physical model and a quoted-price robustness band.**

## 6. Public-data probe

The reproducible probe is [sim/probe_prediction_markets.py](../sim/probe_prediction_markets.py).
It samples closed multi-day binary markets from deterministic Gamma API pages,
keeps one high-volume market per event, and reads public YES-price histories.
The generated observations and exclusions are in
[`data/polymarket_probe.json`](../data/polymarket_probe.json).

The probe is intentionally allowed to return “uninformative.” It does not:

- infer credit calibration from sports or political calibration;
- treat final volume as historical order-book depth;
- turn a binary outcome into fractional recovery;
- call within-contract price evolution a maturity term structure; or
- claim independence after merely deduplicating event identifiers.

The direct credit test requires a materially sized sample of dated default or
recovery markets. A real term-structure test requires the same proposition at
several maturities, not several markets in one event. Historical depth requires
order-book snapshots, not prices alone.

The 2026-10-14 screening run saw 3,100 closed markets and retained 60
seven-day-or-longer markets after event deduplication. All 60 had price
histories, with a median 105.5 observations. At seven days before close, 59
markets were usable: Brier score was `0.211` and binned expected calibration
error was `0.075`. The higher-volume half was not better in this sample
(`0.233` Brier versus `0.191` below the median). Those figures must not be
generalized: the descending-ID sample was concentrated in short-horizon tennis
match markets, contained zero credit-keyword markets, supplied no 30-day or
one-day snapshots under the staleness rule, and contained no explicit
multi-maturity event group. It therefore measured one narrow calibration slice
and returned **uninformative** on credit recovery, liquidity persistence, and
term structure. That negative is useful: a generic resolved-market backtest
cannot validate the proposed credit venue.

## 7. Adversarial model

[sim/liquidity_consol.py](../sim/liquidity_consol.py) adds a deliberately small
screening model:

- a fixed-spread maker is picked off when its stale bid or ask crosses the next
  informed fair value;
- fees offset only part of that adverse-selection loss;
- depth withdraws below a capital floor;
- support for the venue's own persistence quote costs consolidated assets;
- support-induced issuance is reported separately;
- oracle failure consumes maker capital; and
- native reserve value falls with the same information shocks and capital
  impairment that threaten the venue.

The model compares native and external collateral on common random draws and
sweeps fee rate, spread, and manipulation intensity. It is a hostile screening
model, not a calibrated forecast. Its preregistered screening row passes only
when ruin probability is at most `5%`, tenth-percentile recovery is at least
`90%`, and fees cover adverse-selection loss. These are prototype gates, not
claims about optimal regulation.

Results are generated by:

```
.venv/bin/python sim/run_liquidity_consol.py
```

and written to `sim/out/liquidity_consol_summary.json`. Any conclusion below
must state sensitivity, because token-shock coefficients and strategic behavior
are not identified from data.

At the round baseline, external collateral produced mean recovery `0.931`,
tenth-percentile recovery `0.779`, and maker ruin probability `0.120`. The same
random paths with native collateral produced mean recovery `0.424` and
tenth-percentile recovery `0.172`; the difference comes from the reserve mark,
not different trading paths. Mean absolute terminal YES inventory was `0.429`.
Fees covered only `0.202` of modeled adverse-selection loss. The maker therefore
faces both picked-off-quote loss and settlement risk from the inventory left by
nominally symmetric quoting.

Three of 54 sensitivity rows passed all three screening criteria. Every passing
row used external collateral and zero quote-support spending; none used native
collateral. Passing required a modeled fee of at least `5%` of traded notional
with spread `0.02`, or a `10%` fee with spread at most `0.04`. Any positive
support intensity failed at least one gate; high support intensity caused ruin
in most or all paths even when fee coverage exceeded one. These are not
calibrated fee recommendations. They show that a viable externally backed maker
can be constructed by assumption, while native backing and self-support remain
wrong-way exposures across the tested grid.

## 8. Application map

### Sovereign

Use separate objects for default arrival and recovery. A binary “full recovery”
claim discards restructuring and timing information. Compare against CDS,
digital default swaps, recovery swaps, and bond-implied term structures before
claiming new information.

### Payment processor

Define failure as an objective service or settlement event, not bad press or a
token price. Recovery should include safeguarded customer funds, merchant
receivables, and operational restart. The oracle must not be controlled by the
processor or venue.

### Payment corridor

The deliverable is joint: origin access, destination access, FX conversion,
compliance, and final settlement. Shared banks, chains, stablecoins, and legal
regimes create common shocks. Use a joint simulation or observed joint event;
do not multiply marginal uptime probabilities.

### Portfolio

An index reduces idiosyncratic event volatility but can concentrate venue,
oracle, collateral, and legal risk. Diversification of subjects is not
diversification of infrastructure.

## 9. What remains worth doing

Do not build a new exchange or probability perp. The next cheapest
discriminating test is a paper comparison of one externally collateralised
market-maker bond against an ordinary LP/default-fund claim under identical
fees, withdrawal rules, and stress flow.

Continue only if the consol version shows at least one predeclared advantage:

- more executable stressed-state depth per outside collateral dollar;
- lower oracle-plus-liquidity subsidy for equal calibration;
- a payoff investors cannot obtain more simply from the replication set; or
- better isolation of venue survival from underlying credit risk.

If none appears, retain the useful narrower project: a term-structured
credit-information venue with transparent liquidity and resolution budgets.
That may be beautiful infrastructure, but it is not evidence for a new monetary
or credit primitive.

## Sources checked for this memo

- Repository model and negative results:
  [MODEL.md](MODEL.md), [OPEN_PROBLEMS.md](OPEN_PROBLEMS.md),
  [PRIOR_ART.md](PRIOR_ART.md), and [IDEAS.md](IDEAS.md).
- Polymarket API: [market listing](https://docs.polymarket.com/api-reference/markets/list-markets-keyset-pagination),
  [price history](https://docs.polymarket.com/api-reference/markets/get-prices-history),
  and [resolution state](https://docs.polymarket.com/api-reference/markets/get-resolution-state).
- Polymarket mechanism descriptions:
  [liquidity rewards](https://docs.polymarket.com/programs/liquidity-rewards)
  and [resolution](https://docs.polymarket.com/concepts/resolution).
- Page and Clemen, “Do Prediction Markets Produce Well-Calibrated Probability
  Forecasts?”, *Economic Journal* 123 (2013), 491–513.
- Tetlock, “Liquidity and Prediction Market Efficiency,” on calibration,
  resolution, and adverse selection in limit orders.
- Pan and Singleton, “Default and Recovery Implicit in the Term Structure of
  Sovereign CDS Spreads,” *Journal of Finance* 63 (2008), 2345–2384.

The API and mechanism statements are current-documentation checks, not a legal
or operational audit. The empirical papers establish that horizon, liquidity,
and selection matter; they do not validate this instrument.
