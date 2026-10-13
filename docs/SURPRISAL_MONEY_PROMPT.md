# Prompt: Build the "Surprisal Money" repository

You are an agent tasked with creating and iterating on a small research repository. The repository explores a monetary design in which currency is credit against future energy delivery, and in which the issuance limit is set mechanically by the information-theoretic *surprisal of delivery* as priced by a prediction market. Read this whole document before writing anything. Where the spec is silent, prefer the simplest choice that keeps the model honest, and record the choice in `docs/DECISIONS.md`.

The repository must contain three deliverables:

1. `README.md`: a short explainer and rationale for a general technical reader.
2. `docs/MODEL.md`: the in-depth explainer that captures the concrete model below, with equations.
3. `sim/`: a runnable simulation of the single-issuer economy, with a second-issuer extension.

Do not overclaim. This is a toy model intended to make a conceptual argument precise, not a proposal that is ready for anything. Do not invent empirical numbers, historical precedents, or institutional endorsements. Where a claim is a conjecture, label it as one.

---

## 1. The idea in one paragraph (for `README.md`)

Money is credit: a claim on future output. Proposals to "back" money with energy get the substrate right but miss that a joule is only valuable inside a structure that can convert it into something wanted (a grid, a legal system, a supply chain, a functioning city). The value of a currency is really a claim on the persistence of such structures, which are improbable, decay by default, and must be continuously maintained. This persistence is not measurable directly, but it *is* priceable: if a prediction market quotes the probability that a promised delivery will occur, then the surprisal of delivery, −log p, is a well-defined quantity that rises as structures degrade or as an issuer over-promises. The design ties monetary issuance to a budget on aggregate surprisal. The result is a currency that is elastic while the underlying structure is healthy and becomes inelastic the moment it is not, with the constraint enforced by market prices rather than by discretion.

---

## 2. Background argument (for `README.md`, expanded in `docs/MODEL.md`)

Present the following chain of reasoning. Each step should be a paragraph, not a bullet.

**Money as credit.** Following the anthropological account (Graeber's *Debt* is the standard reference), money systems have overwhelmingly been credit systems: ledgers of obligation across time. Fiat is the current experiment in that lineage, not a departure from a metallic norm. The recurring failure mode of credit systems is that the term structure of obligations drifts away from the underlying capacity to honour them.

**Energy as substrate, structure as value.** Thermodynamic and "energy standard" proposals (Ford 1921, Technocracy, Georgescu-Roegen, and recent Bitcoin-adjacent framings) anchor money to energy because energy is conserved and measurable. But a joule delivered into a collapsed economy converts into nothing. What a currency actually claims is the output of low-entropy, anti-entropic structures that channel energy into value. Those structures are specific, path-dependent, and expensive to maintain.

**Two entropies, one confusion.** Thermodynamic entropy and information entropy must be kept apart. Rubble has very high thermodynamic entropy (many microstates realise the same macrostate), yet a prediction about rubble has near-zero information entropy (everyone agrees nothing will be delivered). Because a confident *no* and a confident *yes* are both low-entropy predictions, "minimise the entropy of the outcome distribution" is the wrong objective. The correct quantity is the divergence of the market's distribution from the ideal distribution. With the ideal being a point mass on delivery, KL(ideal ‖ market) = −log p(delivery): the *surprisal of delivery*. This is the only entropy-like quantity used in the model.

**Term structure as implicit pricing of persistence.** A bond promising energy delivery in 100 years is simultaneously a bet that the delivery infrastructure, the enforcing institutions, and the issuer itself will exist in 100 years. Nobody has to measure the entropy of a legal system; the yield required to hold the bond aggregates everyone's beliefs about it. Making the bond energy-denominated rather than fiat-denominated removes the circularity (a dollar defined in dollars) and makes the structural bet explicit, because a joule cannot be inflated away.

---

## 3. The formal model (for `docs/MODEL.md`)

Write this section with equations rendered in Markdown/LaTeX. Keep the notation exactly as below so that the code and the document agree.

### 3.1 Physical economy (single issuer)

Discrete time, t = 0, 1, 2, …

- `E_t`: total energy available to the issuer in period t (exogenous, may be constant or stochastic).
- `S_t ∈ [0, 1]`: structure state. 1 is perfect order, 0 is rubble.
- The issuer splits energy each period: `E_t = E_p,t + E_m,t` (production vs. maintenance).
- Output of the single consumption good ("food"): `Y_t = E_p,t · S_t`.
- Structure dynamics: `S_{t+1} = (1 − λ) S_t + g(E_m,t) · (1 − S_t)`, with `g` increasing, concave, `g(0) = 0`, `g(∞) → 1`. A simple choice: `g(x) = 1 − exp(−κ x)`. Parameters `λ` (decay) and `κ` (maintenance efficiency) characterise the "sovereign".
- Delivery threshold `S_min`: a promise of energy delivery at time t is honoured iff `S_t ≥ S_min`.

### 3.2 Prediction market

For each horizon t there is a binary contract paying one unit of **spot energy at t** if delivery at t occurs. Its price is `p(t)`. Settlement in spot energy (not in the issuer's notes) is what prevents circularity.

Calibration assumption (state it explicitly; it is the bridge between physics and information):

    p(t) = P( S_t ≥ S_min | information at time 0 )

In the simulation, `p(t)` is produced by a forecaster that simulates the structure dynamics forward under a policy assumption plus noise. It must not read the true future.

Derived quantities:

- Surprisal of delivery at horizon t: `u(t) = −log p(t)`.
- Hazard: `h(t) = −Δ log p(t)` (discrete analogue of −d ln p/dt). Constant hazard gives `p(t) = e^{−ht}`, i.e. surprisal linear in maturity.
- Implied yield on a joule-note of maturity t: `r(t) = δ + u(t)/t`, where `δ` is pure time preference. This is the "term structure" of the model.

### 3.3 Money as credit

A **joule-note** of maturity t is an IOU for one joule at time t. Notes are issued by the issuer, circulate against food at value approximately `p(t) × v_t`, where `v_t` is the food price of a spot joule, and are extinguished on delivery. The money supply at any time is the set of outstanding notes: money is a claim on promised future flow and retires itself.

Outstanding notes: `N = { (q_i, t_i) }` with quantity `q_i` and maturity `t_i`.

### 3.4 Issuance rule (mechanical elasticity)

    Σ_i q_i · u(t_i)  ≤  B

The issuer may mint a new note only if the aggregate surprisal of all outstanding notes stays within the budget `B`. Because `u(t)` is near zero when the structure is healthy and well-maintained, issuance is nearly unconstrained in good states. As promises accumulate relative to capacity, or as the structure decays, the forecaster marks `p` down, `u` rises, and the budget binds. Issuance is elastic up to a point and then stops. The position of the wall is set by market-implied confidence, not by discretion.

Note the maturity effect: under constant hazard, a 100-period note consumes 100× the surprisal budget of a 1-period note. Long-dated over-promising is mechanically expensive for weak structures and cheap for strong ones.

### 3.5 The alignment claim (the result the simulation should exhibit)

The only way to restore issuance capacity is to raise `p`, the only way to raise `p` is to raise `S` via maintenance, and raising `S` raises food output. So the issuer's issuance-maximising policy and the welfare-maximising policy point the same direction. State as a conjecture to be checked numerically: under the calibration assumption, an issuer maximising discounted issuance chooses maintenance until the marginal reduction in aggregate surprisal per joule of `E_m` equals the marginal food foregone, and this coincides with the social optimum of `Σ_t β^t Y_t` up to a term that vanishes as the market becomes perfectly calibrated.

### 3.6 Non-delivery

When `S_t < S_min`, notes maturing at t are not honoured. Specify a rule and implement it (e.g. pro-rata partial delivery `min(1, S_t / S_min)` per note, or full default with notes cancelled). The rule feeds back into the forecaster and therefore into `p`. Document the choice.

### 3.7 Multiple issuers and bridges

With issuers `k = 1..K`, each with its own `(λ_k, κ_k, E_k)`, the systemic quantity is the joint surprisal `−log P(all deliver)`. If two issuers share a dependency (a common `E` shock, a shared component of `S`), their delivery outcomes carry mutual information `I(D_j ; D_k) > 0`. A **bridge** is a cross-issuer contract (a note of issuer j exchangeable for a note of issuer k at a rate). The bridge price should carry the mutual-information term: two structures that fail together should not diversify each other. This is the formal statement of "structures first, bridges after."

---

## 4. Simulation specification (for `sim/`)

Language: Python 3.11+. Dependencies: `numpy`, `matplotlib`, optionally `pandas`. No frameworks. Keep the core model in one file with no I/O so it can be imported and tested.

### 4.1 Files

    sim/
      model.py          # Economy, Forecaster, Issuer, Market classes; pure, no plotting
      policies.py       # maintenance policies: constant share, greedy, budget-seeking
      forecaster.py     # Monte-Carlo forecaster producing p(t) from current state
      run_single.py     # single-issuer experiments, writes figures to sim/out/
      run_bridge.py     # two-issuer experiment with shared shock
      tests/test_model.py

### 4.2 Required experiments

**E1. Healthy vs. decaying sovereign.** Two parameterisations with identical `E` but different `λ` (or `κ`). Plot, over time: `S_t`, `Y_t`, the term structure `r(t)` at several snapshots, aggregate surprisal vs. budget `B`, and outstanding notes. Expected qualitative result: the weak sovereign's curve inverts (hazard rises with horizon) and its issuance window closes; the strong sovereign's curve stays flat or gently upward.

**E2. Over-issuance.** Fix the physical parameters; have the issuer attempt to mint aggressively without raising maintenance. Show the budget binding and the term structure moving *before* any physical failure occurs. This is the "feedback is fast" property.

**E3. Maintenance response.** Give the issuer a budget-seeking policy: when the budget binds, divert energy to maintenance. Show issuance capacity recovering and compare discounted food output against the constant-share policy. This tests the alignment conjecture in 3.5.

**E4. Bridge with shared shock.** Two issuers with independent idiosyncratic shocks plus a common shock. Compute (by Monte Carlo) `I(D_j ; D_k)` at several horizons. Show that a naive bridge price built from marginals mis-prices relative to one built from the joint, and that the gap grows with the common-shock share.

### 4.3 Guardrails for the forecaster

- It may use the current state and the issuer's declared policy. It may not read future realised shocks.
- Report its calibration: bin forecast `p` against realised delivery frequency over many runs and include a reliability plot. If the forecaster is badly calibrated, say so; do not tune it to make the results look clean.

### 4.4 Tests

At minimum: conservation (`E_p + E_m = E`), monotonicity (`u(t)` non-decreasing in t under constant hazard), budget rule never violated after issuance, non-delivery rule triggers iff `S_t < S_min`, and forecaster does not access future arrays.

---

## 5. Open problems (for `docs/OPEN_PROBLEMS.md`)

List these honestly. Do not resolve them by fiat; if you make progress, document what changed and what the new failure mode is.

- **Manipulation.** The issuer can buy "yes" contracts on its own delivery to push `p` up and widen the issuance window. Physical settlement means this costs energy when delivery fails, but a large issuer can distort short horizons. Candidate mitigations: caps on issuer participation, a lag between market price and issuance eligibility, or a separate attestation source.
- **Calibration.** Everything rests on `p(t)` tracking `P(S_t ≥ S_min)`. A thin or captured market makes surprisal fictional. The model assumes calibration; a real design would need to earn it.
- **Numeraire and reflexivity.** Spot energy is used as the settlement asset to avoid circularity. In a fuller system the note market and the prediction market interact; check for reflexive loops where the note price feeds the forecast.
- **Non-delivery regime.** The bankruptcy rule changes `p` endogenously. Different rules may produce qualitatively different dynamics; explore at least two.
- **Choice of `B`.** The budget is a free parameter. Is there a principled way to set it (e.g. from the issuer's own posted maintenance commitment), or does it reintroduce discretion through the back door?
- **What the unit of account is.** The model uses joules because they are conserved and measurable. But the value of a joule depends on `S`. Whether a "structured joule" needs its own unit, or whether the term structure already carries all of that information, is unresolved.

---

## 6. Repository layout and conventions

    README.md                  # short explainer + rationale + how to run
    docs/MODEL.md              # in-depth explainer, section 3 above with equations
    docs/OPEN_PROBLEMS.md      # section 5
    docs/DECISIONS.md          # every choice made where this prompt was silent
    docs/REFERENCES.md         # only references you have actually verified exist
    sim/                       # section 4
    LICENSE                    # Apache 2.0

Conventions:

- Precise language. Avoid rhetorical filler and avoid presenting lists of exactly three items as if they were complete; if there are four considerations, list four.
- No fabricated figures, benchmarks, or adoption claims.
- Label conjectures as conjectures. Where a simulation result contradicts the narrative, report the contradiction rather than adjusting the narrative silently.
- Each iteration should leave the repository runnable end to end: `python sim/run_single.py` and `python sim/run_bridge.py` must produce figures without manual steps.

---

## 7. Iteration protocol for future agents

1. Read `docs/DECISIONS.md` and `docs/OPEN_PROBLEMS.md` before changing anything.
2. Pick one open problem or one experiment to extend. State the hypothesis in the PR description or commit message.
3. Run the full experiment suite and the tests.
4. Update `docs/MODEL.md` only if the model changed; update `docs/OPEN_PROBLEMS.md` if a problem was narrowed, resolved, or replaced by a new one.
5. Do not add mechanisms for elegance. Add them only when a specific experiment cannot be run without them.
