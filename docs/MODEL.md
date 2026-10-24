# Model

A toy of one issuer. The code in `sim/` uses the names in the table below. `P` is the physical measure. `Q` is the pricing measure. Where a simulation result contradicts the narrative this file started from, the result is what is reported, and the contradiction is marked.

## Symbol table

| Symbol | Meaning |
| --- | --- |
| `t` | Discrete time, `t = 0, 1, 2, …` |
| `X_t` | Exergy inflow in period `t` |
| `X_p,t`, `X_m,t`, `D_t`, `L_t` | Production, maintenance, delivery, endowment levy. `D_t` includes spot exergy used for early retirement. `X_t = X_p,t + X_m,t + D_t + L_t` |
| `Y_t` | Food output, `Y_t = X_p,t · S_t` |
| `S_t` | Structure in `[0, 1]` |
| `λ`, `κ` | Decay and maintenance efficiency |
| `g(x)` | `1 − exp(−κ x)` |
| `ε_t` | Structure shock: small Gaussian plus a rare negative jump |
| `S_min` | Structural delivery threshold |
| `Ψ(S)` | Structural factor. Regime `R1`: `min(1, S / S_min)`. Regime `R2`: `1[S ≥ S_min]` |
| `Q_t` | Quantity maturing at `t`, including the perp's current payment |
| `φ_t` | Honoured fraction `D_t / Q*_t`, including claims presented for early retirement. Vacuously `1` when `Q*_t = 0` |
| `p^P_s(t)` | `E^P[φ_t \| F_s]`, physical expected delivery |
| `p^Q_s(t)` | Pricing-measure delivery price, `p^P_s(t) / (1 + θ_s)` |
| `θ_s` | Risk-premium wedge, `θ ≥ 0`. One factor per date, common across horizons |
| `u_s(t)` | Surprisal `−log p_s(t)`. The measure is whichever `p` was passed in |
| `h_s(t)` | Forward hazard `u_s(t+1) − u_s(t)` |
| `δ`, `β` | Pure time preference and `β = e^{−δ}` |
| `r_s(t)` | Implied yield `δ + u_s(t) / (t − s)` |
| `M_t` | Note stock `Σ q_i β^{t_i − t}`. A perp contributes `x β / (1 − β)` |
| `p̄_t` | Money-stock-weighted `p^Q` |
| `ℓ(p̄)` | Liquidity service. Threshold form or linear form |
| `P_t` | Price level, notes per unit of food, `M_t / (ℓ(p̄_t) Y_t)` |
| `P*` | Price-level target |
| `U_0 … U_3` | Budget functionals B0–B3 |
| `B̄_t`, `ū` | Ceiling. For B3 the ceiling is the dimensionless `ū` |
| `U^joint` | `−log P(φ_τ ≥ 1 − η` at every outstanding horizon`)` |
| `η` | Tolerance for "full" delivery in the joint event |
| `A_t` | Trailing performance accrual |
| `ρ`, `k` | Relief sensitivity and forecast lag |
| `ζ` | Endowment levy rate |
| `W_t` | Endowment, held in spot exergy |
| `b_t` | LMSR liquidity, proportional to `W_t` |

A perp is a note with no maturity. Its quantity field stores the per-period payment `x`.

## What the objects are

Money here is a set of notes. A dated note is a claim on a quantity of exergy at a date, honoured only to the fraction `φ_t` the issuer can actually deliver. A perp pays a quantity every period and is never extinguished. The note is the unit of account. Exergy is the redemption asset and the settlement asset of the delivery contract. Those are three different roles. If exergy were the unit of account, the exergy price of food would be pinned by structure, `1/S_t`, and there would be no price level for issuance to target.

The issuer's inflow is split four ways. When notes are retired early, `R_t`
is their spot-exergy redemption and `Q*_t = Q_t + R_t` is the total claim
presented for current delivery:

```
X_t = X_p,t + X_m,t + D_t + L_t
Y_t = X_p,t · S_t
D_t = Ψ(S_t) · min(Q*_t, X_t − X_m,t − L_t)
φ_t = D_t / Q*_t
```

Delivery consumes exergy. A large maturity ladder crowds out food. That is the resource constraint that makes promises costly. Maintenance and the levy are rationed down, in proportion, if they exceed the inflow; production is what remains after delivery.

Structure decays unless it is maintained:

```
S_{t+1} = clip( (1 − λ) S_t + g(X_m,t) (1 − S_t) + ε_t , 0, 1 )
g(x) = 1 − exp(−κ x)
```

With `ε = 0` and constant maintenance the fixed point is `S* = g(X_m) / (λ + g(X_m))`, which is strictly below 1 for any finite maintenance. Some hazard remains even in the best steady state. That is why a perp is not free.

`ε_t` has to be random. With deterministic dynamics and a constant inflow, `φ_t` is a known function of the initial state, so a forecast is either 0 or 1 and surprisal is either 0 or infinite. The whole construction is a statement about uncertainty.

## Two measures

The delivery contract pays spot exergy, prorated by `φ_t`. It is not a binary bet, because `φ` is a fraction under both regimes: continuously under R1, and under R2 whenever the inflow cannot cover what was promised. The identification `−log p = KL(ideal ‖ market)` is exact only for a binary outcome. Here `u = −log E[φ]` is a definition, not that divergence.

```
p^P_s(t) = E^P[ φ_t | F_s ]
p^Q_s(t) = p^P_s(t) / (1 + θ_s)
u^Q_s(t) = u^P_s(t) + log(1 + θ_s)
```

`θ_s` is an explicit mean-reverting process that jumps up when `S` is below a reference level. It is not derived from a utility function. The issuer cannot tell, from prices alone, how much of `u^Q` is structural decay and how much is the premium. E5 now sends a fixed physical state and shock path through the live engine while varying only `θ`. The identity above holds to numerical error; in the current output B3 first binds at `θ = 0.5`, while liquidity service falls from about 0.96 to 0.012. The premium moves both the ceiling and money demand.

The forecaster that produces `p^P` is quantity-conditional: it is shown the outstanding book, current maintenance, and the issuer's declared policy, and it draws its own future shocks. It is not shown the shocks the economy will actually realise. On the easy paths used to pick it, both candidate forecasters had Brier scores below `1e-4`, because delivery almost never failed, so the selection barely discriminated. The Monte Carlo forecaster won. The stressed reliability sample currently contains only two populated bins (`0.738 → 0.965` and `0.919 → 0.934` forecast-to-realised), so it shows a large miss in one bin and is not evidence of calibration.

## The yield curve, and what the simulation actually did

```
h_s(t) = u_s(t+1) − u_s(t)
r_s(t) = δ + u_s(t) / (t − s)
```

Constant hazard, `u(m) = h m`, gives a flat yield at `δ + h`. That identity is tested directly. It is not what the simulated economies produce.

If delivery is about equally likely at every horizon, `u` is roughly constant and `r(m) = δ + u/m` falls with maturity by arithmetic. A downward-sloping yield is then not evidence of falling forward hazard. E1 ran a healthy sovereign (`λ = 0.04`) and a weak one (`λ = 0.20`) on the same inflow and the same structure shocks. Final structure was about 0.84 and 0.56. At the initial date the two yield curves coincided, because from `S = 0.75` both still delivered over the forecast window. Later, the weak sovereign's yield slope (`r` at the far lag minus `r` at the near lag) was about `−0.47` and then `−0.57`, against about `−0.04` and `−0.05` for the healthy one.

The prompt this repository was built from predicted the opposite comparative static: a weak sovereign's curve would steepen upward, and genuine inversion would require a regime switch the base model lacks. The simulated curves slope down, and the weak one slopes down more, because its short-maturity surprisal is larger while `u` does not grow linearly. A separate crisis forecast, started inside the transient crisis state, produced both an inverted yield and a falling forward hazard in the corrected timing. Treat the base-model upward-steepening prediction as unsupported here.

## Money demand and the issuance rule

```
p̄_t = (Σ q_i β^{t_i−t} p^Q_t(t_i)) / (Σ q_i β^{t_i−t})
ℓ(p̄) = ℓ̄ / (1 + exp(−(p̄ − p*) / τ_ℓ))
M^d_t / P_t = ℓ(p̄_t) · Y_t
P_t = M_t / (ℓ(p̄_t) · Y_t)
```

`ℓ` is a soft threshold. The linear alternative `ℓ = ℓ̄ · p̄` is implemented and reported as an E3 ensemble robustness run. `p̄` is built from `p^Q`, so the premium contaminates demand as well as the ceiling.

The issuer mints a ladder, by default at lags `{1, 2, 4, 8, 16}`, to hit `M_t = P* · ℓ(p̄_t) · Y_t`, subject to the ceiling. Issuance scale is total face value split across the rungs. If a long ladder is infeasible, shorter ladders are tried. The map from policy action to `M − M_target` can have several roots. A damped local solve records iterations and convergence; a grid scan records every sign change and supplies the fallback. The path keeps the branch nearest the previous action.

The action may be negative. In that case the issuer buys back the shortest claims first at their discounted delivery quote. The exergy paid is early delivery and remains inside `D`, so retirement is neither a free cancellation nor an extra resource outside the accounting identity. Capacity can ration the buyback. E3 reports both issuance and retirement and must still be read as a real-resource experiment: delivery, including early delivery, crowds out food.

The hybrid solver is not reliably convergent on the headline ensemble. At the
`1e-3` target-residual tolerance, median non-convergence is about two thirds of
periods for the target and linear-target policies and one half for repair.
The grid fallback keeps paths runnable, but those periods are approximate policy
actions, not solved equilibria. This is the most important numerical negative in
the corrected run.

## Budget functionals

```
U_0 = Σ q_i u(t_i)
U_1 = Σ q_i u(t_i) β^{t_i−t}
U_2 = Σ q_i (1 − p(t_i)) β^{t_i−t}
U_3 = (Σ q_i u(t_i) β^{t_i−t}) / (Σ q_i β^{t_i−t})
```

B0 and B1 are in exergy-nats, B2 in exergy, B3 in nats per promised unit. A live perp is no longer truncated. Under the forecaster's explicit flat terminal-quote extrapolation, B1–B3 use the exact geometric tail. B0 is infinite whenever terminal surprisal is positive and rejects the perp. E8 separately plots partial sums under constant hazard so the divergence is visible rather than merely asserted.

E4 put a lognormal martingale shock of volatility `σ = 0.2` into `p` and held the physical state fixed. Mean `Δu` was about 0.0226 per step, against `σ²/2 = 0.020`. Mean `Δ(1−p)` was about 0.003. The log functional drifts at approximately the Jensen rate. The shortfall functional does not drift at that rate. It is not exactly driftless, because `p` is clipped away from 0 and 1, which breaks the pure martingale.

E10 runs B1, B2, and B3 on 20 common shock paths and also retains a three-scale sensitivity path. B1 and B2 remain slack at the round baseline values. B3 binds on some stressed paths (its 90th-percentile frequency is about 0.16), producing a wider upper tail of price error. No rule dominates; the comparison remains uninformative wherever all ceilings are slack.

`U^joint = −log P(φ_τ ≥ 1 − η` for every outstanding horizon`)` is computed under the physical measure from Monte Carlo paths and is not what the Q-priced ceilings constrain. Empty probe horizons are excluded. Its additive comparator sums the physical success-event surprisals over the same active horizons. Delivery in this shock structure is positively dependent, which is tested. The inequality reverses under negative dependence; independent and synthetic negative samples keep it from being mistaken for an identity.

## Repair, the levy, and the log-growth conjecture

```
A_t = Σ_{j<t} β^{t−j} [ φ_j − p^Q_{j−k}(j) ]
B̄_t = B̄_0 (1 + ρ A_t)
```

`A_t` is a discounted sum of forecast errors, not a KL divergence. It is an empirical cousin of the gap between realised delivery and the priced law. Relief arrives with lag `k`, so it cannot fund the repair that would have prevented the miss it is scoring.

The headline E3 comparison now holds the maintenance rule fixed so that ceiling relief is the treatment. The older budget-seeking rule remains a separate sensitivity, because changing maintenance at the same time had confounded the first result. Ensemble intervals, including non-convergence frequency, are in `sim/out/summary.json`; they replace single-seed point claims.

The log-growth statement is a conjecture, not a result. Along paths that hold `P*` with rule B3,

```
limsup (1/T) log M_T  ≤  g_Y + limsup (1/T) Σ_s D(P^P_s ‖ P^Q_s)
```

with `D` estimated from binned samples of fractional delivery under the physical and priced laws. Additive smoothing keeps finite samples defined; bin sensitivity remains a limitation. Bernoulli KL between the two means is retained as a labeled secondary diagnostic. The Kelly argument this alludes to (Cover and Thomas, chapter 6) is about a bettor compounding wealth. The issuer is not that bettor. The mapping from ceiling relief to a growth rate remains missing, and `A_t` is a physical-measure forecast error while the priced law sits under `Q`, with `θ` in between. E8 now includes a live perp, but remains a numerical probe rather than a proof.

## Two issuers

E9 now evolves two issuer states under common and idiosyncratic shocks. Bridge delivery is the minimum fractional delivery of the pair, its quote is estimated from that joint law, and B1 converts the quote into an explicit bridge face-value capacity. The product of marginal means supplies the deliberately wrong comparator. Mutual information is reported only as a dependence diagnostic; it is neither fed into the quote nor assumed equal to the capacity gap. If no failure appears in the finite sample, a `1e-12` surprisal floor makes reported capacity finite but economically uninformative.

## Interfaces

- `sim.model.allocate(X, X_m, L, Q, S, S_min, regime, R=0)`
- `sim.model.NoteBook`
- `sim.measures`: `surprisal`, `hazard`, `yield_curve`, `U0`–`U3`, full-tail perp aggregation, `joint_surprisal`, `positive_dependence_gap`, `binary_mutual_information`, `empirical_kl`, `bernoulli_kl`
- `sim.demand`: `ell_threshold`, `ell_linear`, `confidence`, `price_level`, `find_sign_changes`
- `sim.forecaster.Forecaster.forecast(state, book, policy, horizons, rng)` — no future-shock argument
- `sim.manipulation.LMSR`
- `sim.policies.maintenance_share`
