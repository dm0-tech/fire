# Open problems

Grades are about these runs, not about the idea in the abstract. "Headline" means the design is not in a position to shrug the problem off. Nothing here was closed.

## Headline

**Goodhart.** `p^Q` is an input to issuance, and the forecaster does not contain a trader who anticipates that. The calibration sample is a Monte Carlo of the physical model, not a market. Untouched by the experiments. Still the assumption the rest of the construction sits on.

**The risk premium is not reliability.** E5 sends a fixed physical state and shock path through the live engine while varying only `θ`. In the current run B3 first binds at `θ = 0.5`, and `ℓ` falls from about 0.96 to 0.012 as `θ` goes from 0 to 1.5. Prices still do not separate fear from failure. No second information source was added.

**What a delivered unit buys.** Exergy is the redemption asset because it is measurable and is destroyed in use. Its purchasing power in the model is still proportional to `S`, via `Y = X_p S`. The runs do not speak to this. Redeeming into a degraded structure remains a claim on something that produces less food per unit. The design criticises energy-backing and then redeems into exergy. The circularity is smaller, not gone.

**Defending the price target.** The issuer now can buy notes back, shortest first, by spending spot exergy. That closes the purely institutional gap in the first build but exposes the real one: early delivery competes with production and maintenance. E3's ensemble therefore measures both price error and output rather than treating closer targeting as a free improvement.

**Repair does not yet establish recovery.** The corrected headline comparison holds maintenance fixed, so ceiling relief is no longer confounded with a budget-seeking maintenance rule. The latter remains a sensitivity. The fraud story — announce maintenance, do not do it, collect relief — is still not represented by a strategic issuer, and lagged relief still cannot finance the repair that would prevent the current miss.

**Residual manipulation.** E6 now applies the LMSR-adjusted quote inside the live issuance decision and scales attack budgets relative to the current endowment. It reports issuance gained, defense spending, and output drag. This remains a mechanical attacker, not a patient strategic issuer, and the endowment remains a governance target. Hanson and Oprea's informed-trader response is still absent.

**Multiple equilibria and solver failure.** The hybrid solver records local iterations, target residuals, every grid sign change, and fallback use. In E3 the median share of unsolved periods at a `1e-3` residual tolerance is about `0.67` for target, `0.50` for repair, and `0.67` for linear target. The grid fallback keeps the simulation running but does not make those points equilibria. Branch continuity is a numerical convention, not an economic selection mechanism.

## Serious

**Choice of ceiling.** E10 still cannot separate B1 from B2 at the round baseline values: both are slack throughout the ensemble. B3 binds on stressed paths (90th-percentile frequency about 0.16); on the single sensitivity path, halving its ceiling raises mean absolute price error from about 0.005 to 0.163. `B̄_0`, `ρ`, and `ū` remain free parameters, and no overall winner is identified.

**Additivity.** The ceilings still sum across notes. Every live Monte Carlo row now reports joint surprisal and the joint/additive ratio, but issuance does not obey the joint statistic. E9 is the cross-issuer version: it prices the bridge from the joint law and reports the product-of-marginals error.

**Regime dependence.** R1 and R2 are now compared on common 20-seed paths. Any difference is sensitivity evidence, not a principled reason to select one ontology of default.

**The log-growth conjecture.** E8 now includes a live perp and estimates KL from binned fractional-delivery samples, retaining Bernoulli KL only as a labeled diagnostic. The bettor-to-issuer step and the `P`/`Q` mismatch remain untouched, and histogram choices add estimation sensitivity.

**Reflexivity.** E7 now maintains maturity-specific secondary prices and feeds their prior-period values into the forecast. The exit is still imposed rather than chosen by heterogeneous holders, so it tests a causal channel but not strategic run initiation.

**Yield-curve comparative statics.** The prompt predicted that a weak sovereign's curve would steepen upward. E1 produced downward-sloping yields for both sovereigns, steeper for the weak one, because `r = δ + u/m` falls when `u` is large and does not grow linearly. A crisis-conditional forecast produced both inversion and falling forward hazard after forecast timing was corrected. It remains open which term-structure object a monetary design should constrain.

**Heterogeneous holders.** One liquidity demand. No runs in the sense of strategic holders, no flight between issuers. E7's discount is an imposed path, not a decision.

**Forecaster discrimination.** The two forecasters were scored on paths where delivery rarely failed. Brier scores were both below `1e-4`. The Monte Carlo version won by a small margin. A stressed reliability plot shows a miss around a forecast of 0.7. The selection did not establish that the winner is well calibrated where calibration is hard.
