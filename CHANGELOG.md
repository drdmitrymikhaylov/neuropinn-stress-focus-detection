# Changelog

## 2026-11-02

- Added "Where the cut sits": the stability table read at all 27 admissible
  good/poor cuts of the continuous score, not only the published 10 vs 11.6.
  No cut makes any row significant (smallest p 0.094); the degradation d
  (−0.41, the row the power table leans on) runs from −0.65 to +0.36, is
  negative at 15 of 27 cuts and changes sign with the half of the score the
  cut sits in; at the median split all three rows are within ±0.07 of zero.
  Fluctuation on the four-channel montage is the one row negative at every
  cut (−0.71 to −0.01). Bootstrap intervals on the Spearman ρ behind the
  "1 536 / 870 / 5 900 participants" all cover zero and both signs, so those
  figures (and the 95 per group) are point estimates with no finite upper
  bound — stated as such in two places. Degradation's mean difference flips
  sign under a 20 %-trimmed mean (−0.168 → +0.059). Joint permutation: all
  three d negative by chance in 14.0 % of label permutations. The four-channel
  rows of `rank_check.json` are now on the page.
- "What is missing": the stability bullet no longer says "the required sample
  is now known".
- `results/cut_check.json`, `tests/test_cut_check.py` (8 tests; suite 15/15).

## 2026-10-19

- LICENSE now holds the standard CC BY 4.0 legal text, so GitHub recognises the licence (it showed "Other" before). The terms are unchanged; the note on what each licence covers moved to `NOTICE.md`.

## 2026-09-29

- Added "The same table by ranks": the stability table's Cohen's d are
  mean differences; by medians and ranks two of the three rows (level,
  degradation) point the other way — degradation d = −0.41 has rank-biserial
  −0.01, bootstrap CI −1.1 to +0.4, leave-one-out −0.50 to −0.18. Against the
  continuous performance score the metrics correlate at |ρ| ≤ 0.09, which
  needs ~1 500 participants (degradation) rather than 95 per group.
  "Every difference points the way the claim predicts" narrowed to "every
  difference of means".
- Published `results/studies.json` (per-subject values, gate, montage, power)
  and `results/rank_check.json`; `tests/test_readme_numbers.py` (7 tests
  pinning the README numbers to the result files).
