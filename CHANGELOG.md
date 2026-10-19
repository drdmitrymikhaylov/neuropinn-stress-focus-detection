# Changelog

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
