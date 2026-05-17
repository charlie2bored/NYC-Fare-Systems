Objective: To modernize the MTA's revenue structure by replacing the $2.90 flat fare with a distance-based model ($2.00 base + $0.24/mile) to improve fiscal stability and passenger equity.

Key Findings (v2 — Network distance, corrected methodology):

Revenue Surplus: The proposed model generates $4.38 Billion annually, a $913 Million (26.4%) increase over the current flat-fare system. This uses shortest-path distance along the actual NYC subway graph, built from `Master_Stations.csv`.

Commuter Relief: 14.8% of all trips would be cheaper under this model. The breakeven point is 3.75 miles — trips shorter than this become cheaper, longer trips pay more, by construction of the fare formula.

Sensitivity: Re-weighting short trips by 0.5×–1.5× (to test the sample's representativeness) keeps the revenue lift in the $788M–$1,062M range. The directional finding is robust.

---

Key Findings (v1 — Haversine, original methodology, kept for comparison):

Revenue Surplus: The original model generated $3.74 Billion annually, a $277.9 Million (8%) increase over the current flat-fare system.

Commuter Relief: 29% of all trips were cheaper under this model.

Cash Cow Identification: High-volume routes like Penn Station to 5th/53rd (E) remain the system's strongest revenue drivers, justifying tiered pricing in high-traffic corridors.

---

Methodology note: v1 used as-the-crow-flies (Haversine) distance between origin and destination coordinates. v2 measures shortest path along the real subway network. Haversine systematically under-estimates trip length (Flushing → Forest Hills is 2.0 mi crow-flies but 5.9 mi by actual subway), so v1 under-priced long trips and under-stated the revenue case for distance-based pricing.
