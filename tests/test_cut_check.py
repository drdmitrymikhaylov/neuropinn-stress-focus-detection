"""Pin the "Where the cut sits" section to results/cut_check.json and recompute
what can be recomputed from the per-subject values in results/studies.json.

Run with:  python3 -m pytest tests/
Needs numpy and scipy.
"""
import json
import pathlib

import numpy as np
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parents[1]
README = " ".join((ROOT / "README.md").read_text().split())
ST = json.loads((ROOT / "results" / "studies.json").read_text())
CC = json.loads((ROOT / "results" / "cut_check.json").read_text())
RK = json.loads((ROOT / "results" / "rank_check.json").read_text())
FULL = CC["stability_full"]
HEAD = CC["stability_headband"]
METRICS = ("level", "fluctuation_cv", "degradation_per_min")
ZA, ZB = 1.959964, 0.841621  # two-sided 5 %, 80 % power


def cohens_d(x, y):
    nx, ny = len(x), len(y)
    sp = np.sqrt(((nx - 1) * np.var(x, ddof=1) + (ny - 1) * np.var(y, ddof=1)) / (nx + ny - 2))
    return (np.mean(x) - np.mean(y)) / sp


def rank_biserial(x, y):
    u = stats.mannwhitneyu(x, y, alternative="two-sided").statistic
    return 2 * u / (len(x) * len(y)) - 1


def arrays(key, m):
    S = ST[key]["subjects"]
    return (np.array([s["subtractions"] for s in S], float), np.array([s[m] for s in S], float),
            np.array([s["good_counter"] for s in S], bool))


def test_published_cut_is_one_of_the_sweep_rows():
    assert FULL["n"] == 36 and FULL["n_good"] == 26 and FULL["n_poor"] == 10
    assert FULL["published_cut_between"][0] == 10.0 and round(FULL["published_cut_between"][1], 1) == 11.6
    for key in ("stability_full", "stability_headband"):
        for m in METRICS:
            r = CC[key]["metrics"][m]
            row = [x for x in r["cut_sweep"] if x["n_poor"] == 10][0]
            assert abs(row["cohens_d"] - ST[key]["metrics"][m]["cohens_d"]) < 1e-9
            assert abs(row["p_mannwhitney"] - ST[key]["metrics"][m]["p_mannwhitney"]) < 1e-9
            assert abs(r["published"]["cohens_d"] - row["cohens_d"]) < 1e-12


def test_cut_sweep_recomputed_from_subjects():
    """Every admissible cut (>= 5 a side, no tie across it), d and rank-biserial, both montages."""
    for key in ("stability_full", "stability_headband"):
        for m in METRICS:
            score, v, _ = arrays(key, m)
            order = np.argsort(score, kind="stable")
            ss, vs = score[order], v[order]
            rows = CC[key]["metrics"][m]["cut_sweep"]
            mine = []
            for k in range(5, 32):
                if ss[k - 1] == ss[k]:
                    continue
                mine.append((k, cohens_d(vs[k:], vs[:k]), rank_biserial(vs[k:], vs[:k])))
            assert len(rows) == len(mine) == 27
            for row, (k, d, rb) in zip(rows, mine):
                assert row["n_poor"] == k and row["n_good"] == 36 - k
                assert abs(row["cohens_d"] - d) < 1e-9 and abs(row["rank_biserial"] - rb) < 1e-9


def test_sweep_summary_full_montage():
    s = {m: FULL["metrics"][m]["cut_sweep_summary"] for m in METRICS}
    rows = {m: FULL["metrics"][m]["cut_sweep"] for m in METRICS}
    for m in METRICS:
        assert s[m]["n_cuts"] == 27
        assert s[m]["share_of_cuts_with_d_below_zero"] == sum(x["cohens_d"] < 0 for x in rows[m]) / 27
        assert s[m]["min_p"] == min(x["p_mannwhitney"] for x in rows[m])
        assert s[m]["min_p"] > 0.05  # no cut makes any row significant
    # level
    assert (round(s["level"]["d_min"], 2), round(s["level"]["d_max"], 2)) == (-0.23, 0.56)
    assert sum(x["cohens_d"] < 0 for x in rows["level"]) == 20          # 74 %
    assert sum(x["rank_biserial"] < 0 for x in rows["level"]) == 11     # 41 %
    assert round(s["level"]["d_at_median_split"], 2) == -0.07
    assert round(s["level"]["min_p"], 3) == 0.204
    # fluctuation
    assert (round(s["fluctuation_cv"]["d_min"], 2), round(s["fluctuation_cv"]["d_max"], 2)) == (-0.55, 0.18)
    assert sum(x["cohens_d"] < 0 for x in rows["fluctuation_cv"]) == 20       # 74 %
    assert sum(x["rank_biserial"] < 0 for x in rows["fluctuation_cv"]) == 19  # 70 %
    assert round(s["fluctuation_cv"]["d_at_median_split"], 2) == 0.05
    assert round(s["fluctuation_cv"]["min_p"], 3) == 0.094 and s["fluctuation_cv"]["min_p_n_poor"] == 30
    # degradation: the row the power table leans on
    assert (round(s["degradation_per_min"]["d_min"], 2), round(s["degradation_per_min"]["d_max"], 2)) == (-0.65, 0.36)
    assert sum(x["cohens_d"] < 0 for x in rows["degradation_per_min"]) == 15       # 56 %
    assert sum(x["rank_biserial"] < 0 for x in rows["degradation_per_min"]) == 10  # 37 %
    assert round(s["degradation_per_min"]["d_at_median_split"], 2) == -0.05
    assert round(s["degradation_per_min"]["min_p"], 3) == 0.168
    assert s["degradation_per_min"]["largest_abs_d_n_poor"] == 7
    assert [round(c, 1) for c in s["degradation_per_min"]["largest_abs_d_cut_between"]] == [8.6, 9.0]
    # its sign follows the half of the score the cut sits in
    lower = [x["cohens_d"] for x in rows["degradation_per_min"] if x["n_poor"] <= 20]
    upper = [x["cohens_d"] for x in rows["degradation_per_min"] if x["n_poor"] >= 21]
    assert len(lower) == 16 and len(upper) == 11
    assert all(d < 0.005 for d in lower) and sum(d < 0 for d in lower) == 15  # the 16th is +0.004
    assert all(d > 0 for d in upper)
    assert "negative at 15 of the 16 cuts that put 20 or fewer subjects in the poor group" in README
    assert "positive at all 11 cuts above that" in README


def test_sweep_summary_headband():
    fl = HEAD["metrics"]["fluctuation_cv"]
    s, rows = fl["cut_sweep_summary"], fl["cut_sweep"]
    assert all(x["cohens_d"] < 0 for x in rows)                       # 27 of 27
    assert sum(x["rank_biserial"] < 0 for x in rows) == 26            # 96 %
    assert (round(s["d_min"], 2), round(s["d_max"], 2)) == (-0.71, -0.01)
    assert round(s["d_at_median_split"], 2) == -0.19
    assert round(s["min_p"], 3) == 0.122
    lv = HEAD["metrics"]["level"]["cut_sweep_summary"]
    dg = HEAD["metrics"]["degradation_per_min"]["cut_sweep_summary"]
    assert round(100 * lv["share_of_cuts_with_d_below_zero"]) == 78 and round(100 * dg["share_of_cuts_with_d_below_zero"]) == 52
    assert round(100 * lv["share_of_cuts_with_rank_biserial_below_zero"]) == 48
    assert round(100 * dg["share_of_cuts_with_rank_biserial_below_zero"]) == 30
    assert round(min(lv["min_p"], dg["min_p"]), 3) == 0.086
    assert "negative at all 27 cuts (−0.71 to −0.01)" in README


def test_rho_intervals_and_sample_sizes():
    want = {"level": (0.04, -0.33, 0.40, 5872, 47, 42), "fluctuation_cv": (-0.09, -0.43, 0.26, 870, 40, 69),
            "degradation_per_min": (0.07, -0.25, 0.39, 1536, 49, 34)}
    for m, (rho, lo, hi, n_pt, n_edge, share) in want.items():
        r = FULL["metrics"][m]
        assert abs(r["spearman_rho_vs_subtractions"] - RK["stability_full"]["metrics"][m]["spearman_rho_vs_subtractions"]) < 1e-9
        assert round(r["spearman_rho_vs_subtractions"], 2) == rho
        assert round(r["rho_ci95_bootstrap"][0], 2) == lo and round(r["rho_ci95_bootstrap"][1], 2) == hi
        assert r["rho_ci95_bootstrap"][0] < 0 < r["rho_ci95_bootstrap"][1]  # covers zero and both signs
        assert r["n_total_at_rho_point"] == n_pt
        assert r["n_total_at_rho_interval_edge"] == n_edge
        edge = max(abs(r["rho_ci95_bootstrap"][0]), abs(r["rho_ci95_bootstrap"][1]))
        assert int(np.ceil(((ZA + ZB) / np.arctanh(edge)) ** 2 + 3)) == n_edge
        assert round(100 * r["rho_share_of_resamples_below_zero"]) == share
    # the d interval of the previous section, read the same way: 14 per group to no finite number
    lo, hi = RK["stability_full"]["metrics"]["degradation_per_min"]["d_ci95_bootstrap"]
    assert int(np.ceil(2 * ((ZA + ZB) / abs(lo)) ** 2)) == 14 and hi > 0
    assert "about 40–50 participants" in README and "14 per group" in README


def test_location_estimates_recomputed():
    want = {("stability_full", "level"): (-0.182, 0.005, -0.084),
            ("stability_full", "fluctuation_cv"): (-0.040, -0.041, -0.060),
            ("stability_full", "degradation_per_min"): (-0.168, -0.016, 0.059),
            ("stability_headband", "level"): (-0.070, 0.162, 0.285),
            ("stability_headband", "fluctuation_cv"): (-0.074, -0.064, -0.080),
            ("stability_headband", "degradation_per_min"): (-0.107, 0.042, 0.098)}
    for (key, m), (mean, hl, tr) in want.items():
        _, v, good = arrays(key, m)
        g, p = v[good], v[~good]
        r = CC[key]["metrics"][m]["location_differences"]
        assert abs(r["mean"] - (g.mean() - p.mean())) < 1e-9
        assert abs(r["hodges_lehmann"] - np.median(np.subtract.outer(g, p))) < 1e-9
        assert abs(r["trimmed_mean_20pct"] - (stats.trim_mean(g, 0.2) - stats.trim_mean(p, 0.2))) < 1e-9
        assert (round(r["mean"], 3), round(r["hodges_lehmann"], 3), round(r["trimmed_mean_20pct"], 3)) == (mean, hl, tr)
    # degradation flips sign once the tails are trimmed; fluctuation is the only row where all three agree
    d = FULL["metrics"]["degradation_per_min"]["location_differences"]
    assert d["mean"] < 0 < d["trimmed_mean_20pct"]
    f = FULL["metrics"]["fluctuation_cv"]["location_differences"]
    assert f["mean"] < 0 and f["hodges_lehmann"] < 0 and f["trimmed_mean_20pct"] < 0


def test_joint_permutation():
    j = FULL["joint_permutation"]
    assert [round(x, 2) for x in j["observed_d"]] == [-0.18, -0.27, -0.41]
    assert round(j["p_all_three_d_below_zero"], 3) == 0.140
    assert round(j["p_all_three_d_at_most_observed_one_sided"], 3) == 0.016
    assert round(1 / j["p_all_three_d_below_zero"]) == 7
    h = HEAD["joint_permutation"]
    assert round(h["p_all_three_d_below_zero"], 3) == 0.126
    assert round(h["p_all_three_d_at_most_observed_one_sided"], 3) == 0.014
    c = FULL["metric_correlations_pearson"]
    assert round(c["level_fluctuation"], 2) == 0.30
    assert abs(c["level_degradation"]) < 0.10 and abs(c["fluctuation_degradation"]) < 0.10
    assert "14.0 % of permutations" in README and "one time in seven" in README


def test_headband_rank_table_on_the_page():
    h = RK["stability_headband"]["metrics"]
    assert round(h["level"]["cohens_d"], 2) == -0.06 and round(h["level"]["rank_biserial"], 2) == 0.12
    assert [round(x, 2) for x in h["level"]["d_ci95_bootstrap"]] == [-0.94, 0.91]
    assert round(h["level"]["good_median"], 2) == 2.02 and round(h["level"]["poor_median"], 2) == 1.70
    assert round(h["fluctuation_cv"]["cohens_d"], 2) == -0.49 and round(h["fluctuation_cv"]["rank_biserial"], 2) == -0.28
    assert [round(x, 2) for x in h["fluctuation_cv"]["d_ci95_bootstrap"]] == [-1.45, 0.22]
    assert round(h["fluctuation_cv"]["good_median"], 2) == 0.36 and round(h["fluctuation_cv"]["poor_median"], 2) == 0.42
    assert h["fluctuation_cv"]["n_total_for_80pct_power_at_rho"] == 311
    assert h["fluctuation_cv"]["n_per_group_for_80pct_power_at_d"] == 66
    assert round(h["degradation_per_min"]["cohens_d"], 2) == -0.25 and round(h["degradation_per_min"]["rank_biserial"], 2) == 0.06
    assert [round(x, 2) for x in h["degradation_per_min"]["d_ci95_bootstrap"]] == [-1.05, 0.70]
    assert round(h["degradation_per_min"]["good_median"], 2) == -0.10 and round(h["degradation_per_min"]["poor_median"], 2) == -0.22
    assert h["degradation_per_min"]["n_total_for_80pct_power_at_rho"] == 859
    assert h["degradation_per_min"]["n_per_group_for_80pct_power_at_d"] == 246
    assert h["level"]["n_per_group_for_80pct_power_at_d"] == 4596
    assert "| Fluctuation | −0.49 | −1.45 to +0.22 | 0.36 vs 0.42 | −0.28 | −0.16 (*p* = 0.36) | 311 | 66 |" in README
