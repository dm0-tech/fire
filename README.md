# Surprisal money

A toy monetary model. Currency is a set of claims on future delivery of exergy. The price of those claims in a delivery market is treated as information about whether the issuer's structure will still be able to deliver, and issuance is set to hold a price level unless a ceiling on the surprisal of delivery says otherwise. This repository makes that idea precise enough to simulate. It is not a proposal.

The design wants three things. Issuance should expand when delivery is likely, rather than contract. The redemption asset should be something that is scarce because it can still do work, not energy in the conserved sense. And the instrument should have a term structure, including a perpetual, because a perpetual is a claim on persistence itself.

## The argument

Money in the historical record is mostly a ledger of obligations across time, not a warehouse receipt for metal. Credit arrangements fail when the dates on which things are owed drift away from the capacity to honour them. Graeber's *Debt* is the usual telling of that history; the citation is in `docs/REFERENCES.md`.

Anchoring the ledger to energy gets the scarcity wrong. Energy is conserved, so it is not what runs out. Exergy, the part of an energy flow that can still be turned into work, is destroyed as it is used. Even exergy is not enough. A joule delivered into rubble does not become food, transport, or computation. What the note is a claim on is the persistence of the structures that convert exergy into something wanted. Those structures decay unless someone spends resources maintaining them.

Thermodynamic entropy and information entropy are different quantities. Rubble is thermodynamically disordered, and at the same time a forecast about rubble is nearly certain: nothing will be delivered. A confident yes and a confident no are both low-entropy forecasts, so "minimise the entropy of the outcome" points the wrong way. The quantity used here is the surprisal of delivery, `−log p`, which for a binary outcome equals the divergence of the market's distribution from a point mass on delivery. Delivery in the model is a fraction, not a coin flip, so that equality is the motivation and `−log E[φ]` is the working definition.

A note maturing in a hundred periods is a bet that the issuer, the grid, and the institutions around them still exist. The yield required to hold it prices that bet. Settling the delivery contract in spot exergy, rather than in the issuer's own notes, keeps the forecast from being defined in the unit it is forecasting. It does not remove a deeper circularity: the purchasing power of delivered exergy still depends on structure. That remains open.

A ceiling on aggregate surprisal, by itself, is a brake. It loosens when the structure looks healthy and tightens when it does not, which is the usual procyclicality of collateralised credit, not a new virtue. The mechanism in this model runs the other way through money demand. A claim whose delivery is nearly certain does not invite investigation, and that is close to what makes debt usable as money. Higher delivery confidence raises the liquidity service of the note, raises the demand to hold it, and forces the issuer to issue more if it wants the price level held. The durable way to raise that confidence is to spend exergy maintaining the structure. The ceiling stays, as a backstop. The issuer can also retire notes by buying the shortest claims with spot exergy, so contraction is possible but not free.

## What the runs did

Read `docs/MODEL.md` for the equations, `docs/IMPLEMENTATION_AUDIT.md` for the requirement map, and the JSON files in `sim/out/` for current numbers. Closed-form checks establish the Jensen drift and B0's perp divergence. Headline comparisons use 20 common-random-number seeds and 128 forecast paths, report intervals instead of a selected run, compare both default regimes and both liquidity forms, and retain contradictory results. E6 quotes flow through the live issuance decision, E7 observes lagged maturity-specific note prices, and E9 runs coupled issuers with explicit bridge capacity.

`docs/LIQUIDITY_CONSOL_FALSIFICATION.md` applies the same negative-results
discipline to the conjectural venue note in `docs/IDEAS.md`. Its public-data
probe and adversarial collateral comparison are separate from the core model.

## Running it

Python 3.11 or newer is the supported runtime. Dependencies are in `requirements.txt`.

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest
.venv/bin/python sim/run_single.py
.venv/bin/python sim/run_bridge.py
.venv/bin/python sim/run_liquidity_consol.py
.venv/bin/python sim/probe_prediction_markets.py
```

Figures land in `sim/out/`. Core modules under `sim/` do not read or write files; the runners do.
The prediction-market probe requires network access and writes its sampled
observations to `data/polymarket_probe.json`.

`docs/IDEAS.md` is a menu of things one could try to build. Nothing there is an input to the model.
