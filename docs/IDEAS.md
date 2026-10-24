# Ideas

Nothing in `docs/MODEL.md` depends on this file. Nothing here is an input to `sim/`. Grades: **open** means not checked; **conjectural** means a stated mechanism that the toy does not establish; **claimed** means a factual statement about a venue that was checked once and can go stale.

## What a substitute deliverable has to do

Exergy was chosen because it is scarce in the way energy is not. The cost is that no public market quotes dated probabilities of generic exergy delivery, so the simulation invents the market. A substitute has to have a quantity due on a date, a price for the probability of delivery, and a maintained structure whose maintenance the issuer can actually buy. The third test is the one that matters. Without a maintenance lever the instrument is credit with an information-theoretic cap. It is not this design.

**Claimed, narrowly.** For electricity, capacity markets already pay for availability to deliver when called, and congestion or transmission rights are dated claims on delivery across a constrained network. Those are regulated wholesale markets. They are a place to compare the model's `p` with an existing price, not a place to issue a toy currency. Checking that comparison is open.

## Candidates

Each of these is **open** as a design and **conjectural** as a claim that it would reproduce the feedback loop.

- **Blockspace or compute.** A note for a quantity of gas, blobspace, or GPU-hours at a date. The structure is the validator set or the datacenter. The lever is hardware and incentives. Delivery can be read off a chain or a meter.
- **Validator liveness.** A note paid from staking yield, failing on a halt or a slash. Delivery is on-chain, which weakens the Goodhart problem relative to an attested event, without removing it.
- **A resolved question.** The deliverable is a trustworthy answer at a date. The structure is the dispute process and its security budget. This is the candidate closest to the thesis that money is a claim on institutional persistence, and it has the sharpest moral hazard if the issuer funds the oracle that prices the issuer.
- **A basket.** A note redeemable in a portfolio of the above, not in notes. A note redeemable in notes makes `p` undefined. Shared chain risk is exactly the dependence E9 prices badly if one multiplies marginals.

## A liquidity consol

**Conjectural.** A note redeemable for collateral in the prediction market that will exist at date T is a claim that the market will exist, have depth, and resolve. That event is not the same event as the forecast of it, so the construction is self-referential and not circular. Under it, the endowment that provides depth is doing maintenance, because the structure is the market. The repair channel and the funded short side become one mechanism. E6 is the cautionary miniature: the same agent who benefits from a high `p` is funding the book that quotes `p`. Separating two-sided depth at a fixed spread from directional trading is the unsolved piece, and it is unsolved here.

## What is already public

**Claimed, as of the check that went into the source prompt, and stale until re-checked.**

- Polymarket groups binary markets into events. A set of markets on one subject with different end dates is a term structure of the kind `r(m)` is. Survival questions are the persistence bets.
- A strip of YES across those dates resembles a short consol. It is not a perp in the funding-rate sense.
- Historical prices and resolution state are queryable. Binning realised outcomes against prices is the reliability plot this repository only runs on simulated `φ`. It would also be a direct look at the wedge between a traded price and a realised frequency, which is the object's E5 has to invent as `θ`. Doing that binning is the highest-value open measurement on this page. It was not done.

## A perp venue is the other half, and a poor place to start

**Claimed.** Hyperliquid HIP-3 lets a deployer who stakes a large amount of HYPE list a perpetual and define its oracle. The stake is slashable. The protocol's own documentation treats most price indices as poor oracle sources, and assets that move more than about fifty percent in a day, more than rarely, are a poor fit for cross margin. A probability index does that routinely.

**Conjectural, and structural.** A funding-rate perpetual is a rolling claim. It does not produce a curve of `r(m)`. Laddered binaries and a perp are different halves of the model. Listing the perp does not test the term structure, and the term structure is where E1 already disagrees with the verbal story.

## Order of work

1. **Open, cheap.** Pull date-laddered prices and plot `−log p` against maturity. Compare with E1's finding that `r = δ + u/m` falls when `u` is flat.
2. **Open, cheap.** Bin resolved markets against the prices that preceded them. This is the reliability plot on real resolutions, and it is a measurement of the wedge.
3. **Open, no capital.** Run B0–B3 on those price histories, including a perpetual strip truncated the way E8 truncates.
4. **Open, small capital.** List a dated ladder on a venue that already exists.
5. **Open, and not yet.** Deploy a perp on an index. Capital, an oracle that has to be updated, slashing. Only after 1–3 have said something.

## What a deployment would not show

**Conjectural, and the point of the page.** A token whose supply is a function of a market probability will expand in good times and contract in bad times for many reasons that have nothing to do with maintenance. The thesis is the loop from issuance through a maintenance expenditure back to the delivery probability. A deployment that does not name the expenditure, the channel by which it raises `p`, and the change in `p` that would count as a miss, produces a story rather than a test. E3 is the simulated version of that warning: the repair rule was the maintenance channel, and structure did not recover.
