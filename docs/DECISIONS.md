# Decisions

Choices made where the prompt was silent, plus how the section 9 constraints were handled. The constraint record is completed at the end of the build.

## Physical layer

- **Vacuous delivery.** If `Q_t = 0`, then `φ_t = 1`. There is nothing to fail to deliver. Joint-surprisal and confidence calculations skip empty horizons rather than treating this as a success that flatters the issuer.
- **Rationing order.** `X_m` and `L` are chosen before delivery. If they sum to more than `X`, both are scaled down in proportion and delivery takes the residual. Production is the residual after delivery. Delivery crowds out food; maintenance and the levy crowd out both.
- **Extinguishment.** A dated note maturing at `t` is removed whether or not `φ_t = 1`. The unhonoured fraction is a holder loss, not a rollover. Perps are not extinguished.
- **R2 penalty (superseded below).** The first build applied `λ ← λ + Δλ` only when `S_t < S_min`.
- **Shock law.** `ε_t` is `N(0, σ_ε²)` minus `jump_size` with probability `jump_prob`. `X_t` is lognormal with mean `X_mean`. Defaults: `σ_ε = 0.02`, `jump_prob = 0.04`, `jump_size = 0.20`, `σ_X = 0.08`, `X_mean = 1`.
- **Crisis state, for the inversion question only.** A two-state Markov flag. While in crisis the structure shock is shifted down by `crisis_jump`. `p_stay = 0.35`, so a crisis is transient: near-term delivery is worse than distant delivery. Healthy-versus-decaying comparisons leave `p_enter = 0` and never enter the state. This is the regime switch section 3.4 asks for. It is not part of the base sovereign.

## Market and monetary layer

- **Wedge.** `θ` is one non-negative factor per date, common to every horizon at that date: `θ_t = max(0, (1−α) θ̄ + α θ_{t−1} + γ max(0, S_ref − S_t) + σ ξ_t)` with `α = 0.75`, `θ̄ = 0.04`, `γ = 1.2`, `σ = 0.01`, `S_ref = 0.70`. Not derived from a utility function.
- **Probe quantity.** The forecaster is quantity-conditional on the outstanding ladder. A horizon with no outstanding note is forecast as a promise of `q_probe = 0.05 X_mean`, so the term structure is defined before the first mint. Horizons with notes use those quantities, including the perp's per-period payment.
- **Unit of account.** The note. Redemption asset and delivery-contract settlement: spot exergy.
- **Money weights.** `w(m) = β^m`. A perp's stock contribution is `x β / (1−β)`, which excludes the payment being settled this period.
- **No buybacks.** "Retire" means maturing notes extinguish and are not automatically replaced. The issuer cannot repurchase outstanding notes. Defending `P*` by shrinking `M` is therefore only as fast as the ladder runs off. This is a constraint, not a bug to be tuned away.
- **Confidence with an empty book.** `p̄ = 1` when no notes are outstanding. The index is otherwise the money-stock-weighted average of `p^Q`, and a perp is weighted by `x β / (1−β)` at the forecast for the probe horizon nearest the mean maturity of the perp's truncated ladder (horizon 10).
- **KL stand-in.** Delivery is fractional, so `D(P^P ‖ P^Q)` in the log-growth check is the Bernoulli KL between `p^P` and `p^Q` at each horizon, averaged over horizons. That is the binary identity the prompt derives, used as a stand-in for a law on `[0, 1]`. It is not the KL between the full distributions of `φ`.
- **Joint event.** `η = 0.05`. Success at a horizon means `φ ≥ 1 − η`.
- **Default ladder.** New dated issuance is split equally across horizons `{1, 2, 4, 8, 16}`.
- **Fixed point.** Issuance scale is evaluated on a grid. A root is a sign change of `M(s) − M_target(s)`, or an exact zero. Every sign change is recorded. The path selects the root closest to the previous period's scale, which is the basin carried in from yesterday. If there is no root, the issuer mints nothing when `M` already exceeds the target, and otherwise mints the largest scale that respects the ceiling.
- **Ceiling floor.** `B̄_t = max(B_floor, B̄_0 (1 + ρ A_t))` with `B_floor` a small positive number, so a large negative accrual cannot make the ceiling negative.
- **Defaults.** `δ = 0.03`, `ℓ̄ = 1`, `p* = 0.75`, `τ_ℓ = 0.08`, `P* = 1`, maintenance share `0.25` unless a policy says otherwise, `ρ = 0.8` when repair is on and `0` otherwise, `k = 2`, `ζ = 0` unless an experiment turns the levy on, `ū = 0.40` for rule B3. B1's ceiling defaults to `0.80` exergy-nats and B2's to `0.50` exergy. These are round starting values, not calibrated to a result.
- **LMSR numeraire.** LMSR costs are treated as exergy. `b = b_scale · max(W, W_floor)` with `b_scale = 1` and `W_floor = 0.02`, so an empty endowment is a thin market rather than a division by zero.
- **Mutual information.** Delivery outcomes are binarised at `1 − η` before `I(D_j; D_k)` is computed. The bridge price itself uses the joint distribution of `φ`, not `I`.

## Further choices found while building

- **Perp inside the loop.** A perp in the live ceiling is truncated at 30 periods. E8's divergence result uses the untruncated partial sums in `perp_partial`. The truncation is only so B0 does not veto every other experiment.
- **Quantity cap per rung.** Promised quantity at one horizon cannot exceed one period of mean inflow. B3 does not limit quantity, only mean surprisal, so without a cap the price-level rule would be free to mint without bound whenever the ladder's mean surprisal sat under `ū`.
- **Issuance scale.** The grid locates a root of `M − M_target`. The mint uses the interpolated scale, not the nearest grid node.
- **Budget-seeking maintenance.** After a period in which the ceiling bound, the maintenance share rises by 0.20, capped at 0.80. Otherwise it sits 0.05 below the base share. This is why the repair policy can under-maintain relative to a constant share.
- **Forecast seed within a period.** Every scale on the issuance grid is forecast with the same random seed, so the grid varies the book rather than the Monte Carlo draw.
- **Declared future levy.** The forecaster is told a constant future levy share `min(0.5, ζ)`, not the exact future mint.
- **Attack budget in E6.** The attacker's exergy budget is a fixed 0.25. It does not grow with seigniorage.
- **Python.** The suite ran on CPython 3.9. The prompt asks for 3.11+. Postponed annotations are what made that import.

## Section 9 constraints

1. **Prediction-blind experiments.** Not enforced. One session wrote the prompt, the model, and the experiment runners, and knew which qualitative results the prompt expected. The runners report numbers and do not contain a hidden pass that picks the prettiest seed. The comparison with the prompt is in `docs/MODEL.md` and `docs/OPEN_PROBLEMS.md`, written after `sim/out/summary.json` existed, and it includes the contradictions (yield slopes, repair, the slack bakeoff).
2. **Citation pass.** Enforced as a separate pass. Verdicts are in `docs/_citation_verdicts.md`. `docs/REFERENCES.md` and `docs/PRIOR_ART.md` use only the verified entries. The commodity-basket attribution for Keynes is omitted and marked misattributed. Longstaff is cited for what that pass found (default is the majority component in their study), not for the prompt's grouping under "mostly risk premium."
3. **Spec-blind tests.** Not enforced. The same session wrote `sim/model.py` and `sim/tests/test_model.py`. The tests follow the list in section 4.4 of the prompt, including the four-way exergy identity, the flat yield under constant hazard, B0's divergence, and a negative-dependence case that reverses the joint-surprisal inequality.
4. **Single notation owner, first.** Enforced in order, not in personnel. `sim/model.py`, `sim/measures.py`, and the symbol table were written before `demand.py`, the policies, the forecasters, and the experiment runners. One session did all of it.
5. **Narrative audit.** Done in the same session, after the figures. Claims in `README.md` and `docs/MODEL.md` were checked against `sim/out/summary.json` and `sim/out/bridge_summary.json`. The audit was not an independent reader. The contradictions that were written in, rather than smoothed: weak yields slope down rather than up; repair lowers final structure on the reported shock; E8's growth bound holds because money did not outgrow output; E10 does not rank the ceilings; the reliability plot on easy paths is not evidence of calibration; E9's mutual information is not equal to the surprisal gap.

**Forecaster selection.** Two estimators, Monte Carlo and mean field, scored by Brier score on realised `φ`. Monte Carlo won (`3.9e-5` against `6.0e-5`). They were not written in separate worktrees. The scores are close because those paths rarely fail to deliver. The winner was not retuned after the experiments. Experiment runs use 12 Monte Carlo paths as a budget; the selection itself used the class default of 48.

## 2026 correction pass

The following choices supersede the corresponding first-build decisions.

- **Retirement.** The price-target policy may buy notes back. A buyback is an
  early delivery against an outstanding claim, paid in spot exergy and included
  in `D`; it is not costless liability deletion. Short maturities retire first.
  Capacity rationing limits how much of a requested buyback actually occurs.
- **Issuance scale.** Scale is total face value and is split equally across the
  selected rungs. It is no longer an amount repeated on every rung.
- **Empty book.** `p̄` is the mean quantity-conditional probe quote, not one.
- **Solver.** A damped local fixed-point solve is instrumented with iteration
  and convergence fields. A full grid still locates every sign change and is
  the deterministic fallback; branch continuity selects among roots.
- **Perps.** The fixed 30-period truncation is removed. Money uses the full
  geometric stock. B1–B3 use an exact geometric tail under the forecaster's
  explicit flat terminal-quote extrapolation. B0 assigns infinity to a perp
  with positive tail surprisal and therefore rejects it.
- **Divergence.** E8's primary diagnostic is histogram KL between simulated
  fractional physical and priced delivery samples. The priced sample law is an
  explicit deterministic push toward zero or one whose mean is exactly `p^Q`;
  market adjustments rebuild it. Bernoulli KL between means remains in output
  under the name `kl_bernoulli`; it is not represented as the delivery-law
  divergence.
- **R2 penalty.** Any actual non-delivery on a maturing claim, including
  capacity rationing with sound structure, applies `Δλ`. Empty books and
  retirement-only rationing do not count as default.
- **Repair comparison.** E3 holds maintenance fixed across the target and
  target-plus-relief headline policies. Budget-seeking maintenance is a
  separate robustness case.
- **Manipulation budget.** E6 sweeps attack capacity relative to the current
  exergy endowment. The LMSR-adjusted quote enters live demand and ceiling
  decisions; defense spending reduces `W`.
- **Reflexivity.** E7 feeds lagged, maturity-specific secondary prices to the
  forecaster. A holder exit is a haircut to those prices, not a direct scalar
  multiplier on `p^Q`.
- **Bridge.** E9 runs coupled issuers with common and idiosyncratic shocks,
  prices the bridge from joint fractional delivery, and computes bridge
  issuance capacity. Mutual information remains diagnostic.
- **Evidence budget.** Headline comparisons use 20 common-random-number seeds
  and 128 Monte Carlo forecast paths, reporting percentile intervals. This pass
  runs on Python 3.11+. The first build's Section 9 provenance limitations
  remain historical facts.
