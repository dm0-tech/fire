# Implementation audit

Audit target: `SURPRISAL_MONEY_PROMPT.v2.md`, sections 3 and 4. The baseline
was Python 3.9.6 with 14 passing tests. The corrected build is also exercised
on Python 3.11 and records runtime metadata in its output summaries.

## Requirement map

- **Physical accounting and delivery (3.1–3.2): implemented.** The engine
  records the four-way identity each period. Early retirement is a delivery
  against an outstanding claim and is included in `D`, rather than deleting a
  liability for free. R1 and R2 are both covered and compared on common paths.
- **Two measures and quantity conditioning (3.3): implemented.** Forecasts
  retain physical and priced fractional-delivery samples. Behavioral tests
  verify that promised quantity changes the forecast and that realized future
  arrays are not an input.
- **Term structure (3.4): implemented, original prediction contradicted.**
  Constant hazard gives a flat yield in the regression test. Simulated weak
  issuers need not steepen upward; the generated evidence remains authoritative.
- **Money, demand, and perps (3.5): implemented.** Empty-book confidence uses
  the probe curve. Threshold and linear liquidity forms are compared. Perps use
  their full geometric money weight and analytic flat-forecast tails in B1–B3;
  B0 rejects a nontrivial perp as infinite.
- **Issuance and retirement (3.6): partial, with diagnostics.** Scale is
  total face value split across rungs. A damped local solve records residual
  behavior and convergence, while an all-root grid scan supplies multiplicity
  and fallback behavior. Retirement is capacity-constrained and paid in exergy.
  E3 still has median target-residual failure rates of 0.50–0.67 for the
  demand-targeting variants; fallback periods are not solved equilibria.
- **Budget rules and dependence (3.7): implemented.** Every Monte Carlo engine
  row reports physical-measure additive and joint success-event surprisal over
  the outstanding horizons, their ratio, and the event probability. Empty probe
  horizons are excluded. The Q-priced ceiling remains additive by design.
- **Repair (3.8): implemented.** Headline comparisons hold maintenance fixed;
  the adaptive rule is a separate sensitivity rather than a confound.
- **Funded short side (3.9): implemented as a toy market.** LMSR quotes enter
  the same-period ceiling and demand calculations. Levy receipts fund defense,
  defense spending reduces the endowment, and E6 sweeps attack budget relative
  to the endowment while reporting issuance and output.
- **Growth conjecture (3.10): diagnostic only.** E8 is perp-inclusive and uses
  histogram KL on fractional physical samples and an explicit deterministic
  priced-law transform whose mean matches the wedge quote exactly.
  Bernoulli-on-mean KL remains separately labeled; neither estimate proves the
  conjecture.
- **Two issuers (3.11): implemented as a coupled extension.** Issuers receive
  common and idiosyncratic shocks. A bridge is priced from joint fractional
  delivery and its B1 issuance capacity is compared with a marginal-product
  approximation. Mutual information is diagnostic, not a price.

## Experiment status

E1–E3 and E5–E8 now use live engine paths; E4 remains a deliberately isolated
closed-form validation. E9 uses the coupled bridge engine. E10 compares common
shock ensembles. Headline summaries use 20 seeds, 128 forecast paths, common
random numbers, and 10th/50th/90th percentile reporting.

## Remaining limitations

The LMSR and secondary-note markets are still stylized rather than strategic
agent markets. The fractional-law KL uses bins and must be read with its
bin-sensitivity caveat. The bridge capacity mapping is a B1 accounting
experiment, not a proof of the side-information conjecture. The original build
was not prediction-blind or spec-blind; later independent audits improve
verification but cannot retroactively change its provenance.
