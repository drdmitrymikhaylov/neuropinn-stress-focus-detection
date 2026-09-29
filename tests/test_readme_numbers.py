"""Pin the numbers quoted in README.md to the result files, so they cannot drift.

Run with:  python3 -m pytest tests/
Needs numpy and scipy.
"""
import json
import pathlib

import numpy as np
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text()
ST = json.loads((ROOT / "results" / "studies.json").read_text())
RK = json.loads((ROOT / "results" / "rank_check.json").read_text())
FULL = RK["stability_full"]["metrics"]
HEAD = RK["stability_headband"]["metrics"]


def test_group_sizes_and_split():
    assert RK["stability_full"]["n_good"] == 26 and RK["stability_full"]["n_poor"] == 10
    assert RK["stability_full"]["split"]["poor_max_subtractions"] == 10.0
    assert round(RK["stability_full"]["split"]["good_min_subtractions"], 1) == 11.6
    s = [x["subtractions"] for x in ST["stability_full"]["subjects"]]
    assert round(min(s)) == 1 and round(max(s)) == 35
    assert "run continuously from 1 to 35 and are cut at 10 vs 11.6" in README


def test_d_values_match_stability_table():
    m = ST["stability_full"]["metrics"]
    assert round(m["level"]["cohens_d"], 2) == -0.18
    assert round(m["fluctuation_cv"]["cohens_d"], 2) == -0.27
    assert round(m["degradation_per_min"]["cohens_d"], 2) == -0.41
    for k in ("level", "fluctuation_cv", "degradation_per_min"):
        assert abs(FULL[k]["cohens_d"] - m[k]["cohens_d"]) < 1e-9
        assert abs(FULL[k]["p_mannwhitney_two_sided"] - m[k]["p_mannwhitney"]) < 1e-9
    assert round(m["level"]["p_mannwhitney"], 2) == 0.99
    assert round(m["degradation_per_min"]["p_mannwhitney"], 2) == 0.99


def test_rank_table():
    assert round(FULL["level"]["rank_biserial"], 2) == 0.01
    assert round(FULL["fluctuation_cv"]["rank_biserial"], 2) == -0.19
    assert round(FULL["degradation_per_min"]["rank_biserial"], 2) == -0.01
    assert round(FULL["level"]["good_median"], 2) == 1.81 and round(FULL["level"]["poor_median"], 2) == 1.77
    assert round(FULL["fluctuation_cv"]["good_median"], 2) == 0.31 and round(FULL["fluctuation_cv"]["poor_median"], 2) == 0.37
    assert round(FULL["degradation_per_min"]["good_median"], 2) == -0.01
    assert round(FULL["degradation_per_min"]["poor_median"], 2) == -0.13
    # medians point against the means for level and degradation, with them for fluctuation
    assert FULL["level"]["good_median"] > FULL["level"]["poor_median"]
    assert FULL["degradation_per_min"]["good_median"] > FULL["degradation_per_min"]["poor_median"]
    assert FULL["fluctuation_cv"]["good_median"] < FULL["fluctuation_cv"]["poor_median"]


def test_spearman_with_continuous_score():
    subj = ST["stability_full"]["subjects"]
    score = [x["subtractions"] for x in subj]
    for k, want in (("level", 0.04), ("fluctuation_cv", -0.09), ("degradation_per_min", 0.07)):
        rho = stats.spearmanr(score, [x[k] for x in subj]).correlation
        assert round(rho, 2) == want
        assert abs(FULL[k]["spearman_rho_vs_subtractions"] - rho) < 1e-9
        assert abs(rho) < 0.10
    assert round(FULL["level"]["spearman_p"], 2) == 0.83
    assert round(FULL["fluctuation_cv"]["spearman_p"], 2) == 0.58
    assert round(FULL["degradation_per_min"]["spearman_p"], 2) == 0.68
    assert round(HEAD["fluctuation_cv"]["spearman_rho_vs_subtractions"], 2) == -0.16
    assert round(HEAD["fluctuation_cv"]["rank_biserial"], 2) == -0.28


def test_bootstrap_and_leave_one_out_on_degradation():
    r = FULL["degradation_per_min"]
    assert round(r["d_ci95_bootstrap"][0], 1) == -1.1 and round(r["d_ci95_bootstrap"][1], 1) == 0.4
    assert round(r["d_leave_one_out_min"], 2) == -0.50 and round(r["d_leave_one_out_max"], 2) == -0.18
    assert "between −0.50 and −0.18" in README
    lvl = FULL["level"]
    assert round(lvl["d_ci95_bootstrap"][0], 2) == -1.11 and round(lvl["d_ci95_bootstrap"][1], 2) == 0.61
    fl = FULL["fluctuation_cv"]
    assert round(fl["d_ci95_bootstrap"][0], 2) == -1.16 and round(fl["d_ci95_bootstrap"][1], 2) == 0.38


def test_sample_sizes():
    # the power table in the README (per group, from d)
    assert FULL["degradation_per_min"]["n_per_group_for_80pct_power_at_d"] == 95
    assert FULL["fluctuation_cv"]["n_per_group_for_80pct_power_at_d"] == 220
    assert FULL["level"]["n_per_group_for_80pct_power_at_d"] == 459
    assert ST["power"]["degradation_per_min"]["n_per_group_for_80pct"] == 95
    # the totals implied by the correlations with the continuous score
    assert FULL["degradation_per_min"]["n_total_for_80pct_power_at_rho"] == 1536
    assert FULL["fluctuation_cv"]["n_total_for_80pct_power_at_rho"] == 870
    assert round(FULL["level"]["n_total_for_80pct_power_at_rho"], -2) == 5900
    assert "degradation (1 536), 870 for fluctuation and 5 900 for level" in README
    # Fisher-z sample size recomputed independently for the degradation row
    rho = abs(FULL["degradation_per_min"]["spearman_rho_vs_subtractions"])
    n = int(np.ceil(((1.959964 + 0.841621) / np.arctanh(rho)) ** 2 + 3))
    assert n == 1536


def test_montage_margin_column():
    m = ST["montage"]
    full = m["full_19"]["auc"] - 0.5
    assert round(100 * (m["wearable_3ch"]["auc"] - 0.5) / full) == 77
    assert round(100 * (m["wearable_4ch"]["auc"] - 0.5) / full) == 65
