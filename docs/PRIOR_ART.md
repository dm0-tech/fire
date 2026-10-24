# Prior art

Organised by the objection, not by date. Citations are only those in `docs/REFERENCES.md`, which lists works a separate pass confirmed exist and say what is claimed. One attribution in the source prompt did not survive that pass; it is at the bottom.

## Moneyness wants information-insensitivity

Holmström's argument is that debt used as money works because it does not invite price discovery: over-collateralised, information-insensitive claims circulate without anyone needing to produce private information about them. Gorton describes a banking panic as that regime breaking, so that quantities (haircuts, renewals) move once the debt can no longer be held without investigation. Dang, Gorton, and Holmström put the same point as a design principle: debt is the least information-sensitive contract, and a crisis is the moment it becomes sensitive.

This is the strongest objection to repricing a currency, continuously, off a prediction market. The model's answer is to turn the objection into the demand curve. Liquidity service `ℓ(p̄)` is high only when delivery confidence is high, which is the region where the note is least worth investigating. The objection is not answered in the middle, where `p̄` sits near the threshold and the note is neither confidently good nor confidently bad. E5 shows `ℓ` collapsing as the priced probability falls, including when the fall is a risk premium rather than a change in physical delivery. That is the objection arriving through the demand channel.

## Real bills do not pin the price level

"Notes retire when the goods are delivered" is the real-bills doctrine. Sargent and Wallace set it against the quantity theory and, in their examples, find a real-bills regime Pareto optimal even while prices move more. Mints named the doctrine and argued that restricting banks to real commercial paper does not by itself produce the right quantity of money. Fullarton, on the Banking School side, held that notes issued against real transactions flow back to the issuer. Thornton argued that discounting real bills does not limit the issue, because the demand for paper can expand with prices.

The model does not claim that self-liquidation pins the price level. It adds an explicit target `P*` and a quantity equation. E3 is what that target is worth when notes cannot be repurchased: the mean absolute price gap under the target was about 13, not zero.

## Money has to be essential

Kiyotaki and Wright's search model is one place the question "why hold the token at all" is posed rather than assumed. Lagos and Wright keep that friction and make it usable for policy. Kocherlakota's result is that money is a limited form of memory of trading histories. The model does not microfound any of this. It puts a liquidity service on the note so that circulation is not an assumption with no argument attached. That is a reduced form, and it is labelled as one.

## Collateralised credit tightens in bad states

Bernanke, Gertler, and Gilchrist describe a financial accelerator in which agency costs rise in downturns and credit shifts toward borrowers who are easier to monitor. Brunnermeier and Pedersen name a margin spiral in which price moves, margins, and funding liquidity feed each other. Kiyotaki and Moore have durable assets serving as both input and collateral, so prices and credit limits amplify each other. Minsky's instability hypothesis is that quiet expansions shift financing toward structures that cannot survive a disappointment. Adrian and Shin document procyclical leverage at marked-to-market intermediaries.

A surprisal ceiling that tightens as `p` falls is this family of mechanisms. The model keeps the ceiling and tries not to let it be the policy. On the reported path the pure ceiling produced worse output and a much worse price gap than the price-level rule. It did not produce a tidy one-for-one contraction of money with demand. The price level blew out, because the stock of notes stayed large while food was crowded out by delivery.

## A target stops measuring what it measured

Goodhart's statement is that a statistical regularity tends to collapse once it is pressed into service as a control. (The slogan that a measure ceases to be good the moment it is a target is a later paraphrase.) Lucas's critique is the same issue in a different formal language: relations used to evaluate a policy embed expectations of the policy regime and change when the regime changes.

Once `p^Q` sets issuance, `p^Q` is a price of the policy game as well as of delivery. The model has no traders who know the issuance rule and trade it. The forecaster conditions on the declared maintenance share. That is not a defence against Goodhart. It is the assumption the objection says will fail.

## Prediction markets can be pushed, and pushing them is not only harmful

Hanson's logarithmic market scoring rule is the market implemented in `sim/manipulation.py`. Hanson and Oprea show a case in which a manipulator with a noisy target raises the return to being informed, so accuracy can improve. Wolfers and Zitzewitz give conditions under which a binary contract's price is near the mean belief. Ottaviani and Sørensen show a setting in which prices under-react to information when priors differ and budgets are limited, so the price is not a Bayesian aggregate.

E6 is the mechanical version of the payoff asymmetry, not the Hanson–Oprea theorem. With no endowment, a fixed attack budget drove the LMSR price from 0.75 to about 1. With the small endowment accumulated at a levy `ζ = 0.05`, the same budget was walked back to the fair price. Discounted output fell as `ζ` rose (about 6.73 at zero, about 6.44 at `ζ = 0.4`). A thin LMSR is cheap to move in both directions, so this does not show that a large issuer cannot outspend the endowment. It shows that, against this fixed budget, a small levy was enough, and it was not free.

## Spreads are not expected loss

Gilchrist and Zakrajšek decompose a corporate spread index into a part associated with expected default and a residual excess bond premium. That is the empirical shape of the wedge `θ`: the price is not the physical expectation. Longstaff, Mithal, and Neis also separate a default component from a non-default component, using credit default swaps. They find default to be the majority of the spread in the categories they study, plus a remaining non-default piece. They do not support a claim that spreads are mostly something other than default. The model's wedge is a modelling choice in that disputed range, not a fact taken from one of these papers.

## Log-optimal growth

Kelly's 1956 paper is the growth-rate argument: a bettor who bets his beliefs against fair odds grows at a rate given by the information the odds failed to price. Cover and Thomas, chapter 6, state the growth gap as the relative entropy `D(p ‖ q)` and the value of side information as the mutual information. Sections 3.10 and 3.11 of the model are conjectures that point at those theorems. They are not instances of them. E8 satisfied the proposed inequality because money grew slightly slower than output. E9's mutual information rose with the common shock and was not equal to the gap in joint surprisal.

## Exergy, entropy, and earlier monetary anchors

Georgescu-Roegen's theme is that economic activity uses low-entropy resources and is not a mechanical cycle. Ayres and Warr argue that useful work, exergy converted at the point of use, accounts for growth that an energy measure plus a residual does not. Landauer's principle is that logically irreversible operations have a heat cost; it is cited only as a warning not to treat information and thermodynamics as the same ledger. The model uses exergy as the scarce inflow and uses surprisal as a separate, information-theoretic ceiling. It does not derive one from the other.

Ford, in a 1921 newspaper interview, proposed currency issued against energy rather than gold. Hayek's *Denationalisation of Money* argues for competing private currencies whose issuers survive by preserving value. Keynes's bancor is the unit of an International Clearing Union for settling balances between countries. It is not a commodity-basket currency. That last point is the failed attribution below.

Graeber's argument, used in the README, is that credit ledgers precede coinage in the historical sequence, against the textbook order of barter, then money, then credit.

## Misattributed

The source prompt grouped Keynes with "commodity-basket proposals." The bancor plan is not a basket standard. A commodity-reserve currency is a different proposal (associated with Benjamin Graham) and was not verified here, so it is not cited.
