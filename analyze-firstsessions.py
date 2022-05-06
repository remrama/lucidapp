"""Run statistics comparing lucidity across conditions for the first few nights.
"""
import os
import itertools
import numpy as np
import pandas as pd
import pingouin as pg

import utils


#### Choose import/export paths.
import_fname = os.path.join(utils.Config.data_directory, "derivatives", "session_lucidity.csv")
export_fname1 = os.path.join(utils.Config.data_directory, "results", "analyze-firstsessions_within.csv")
export_fname2 = os.path.join(utils.Config.data_directory, "results", "analyze-firstsessions_between.csv")

#### Load data.
df = pd.read_csv(import_fname)

# Reduce to first 2 sessions (dropping anyone without both).
df = df[df["sessionID"].isin([1,2])]
df = df[df["subjectID"].duplicated(keep=False)]

# Get a single difference score for each participant
# that represents their change from session 1 -> session 2.
change = df.pivot(columns="sessionID", index=["subjectCondition", "subjectID"]
    ).diff(axis=1).droplevel(0, axis=1)[2].rename("sessionChange")


def pval_from_distribution(dist):
    pct_below = np.mean(dist < 0)
    pct_above = np.mean(dist > 0)
    min_pct = np.min([pct_below, pct_above])
    pval = 2 * min_pct
    return pval

within_results = []
for c, ser in change.groupby("subjectCondition"):
    ci, distr = pg.compute_bootci(ser.values,
        seed=0,
        func="mean", n_boot=2000, decimals=2, return_dist=True)
    within_results.append({
        "subjectCondition": c,
        "n": ser.size,
        "mean": np.mean(distr),
        "ci_lo": ci[0],
        "ci_hi": ci[1],
        "pval": pval_from_distribution(distr),
    })

within_df = pd.DataFrame(within_results)


between_results = []
conditions = ("active", "control", "sham")
for c1, c2 in itertools.combinations(conditions, 2):
    a = change.loc[c1].values
    b = change.loc[c2].values
    ci, distr = pg.compute_bootci(a, b,
        seed=1,
        func="cohen", n_boot=2000, decimals=2, return_dist=True)
    between_results.append({
        "subjectCondition1": c1,
        "subjectCondition2": c2,
        "mean": np.mean(distr),
        "ci_lo": ci[0],
        "ci_hi": ci[1],
        "pval": pval_from_distribution(distr),
    })

between_df = pd.DataFrame(between_results)



# Export both files.
within_df.to_csv(export_fname1, na_rep="NA", float_format="%.4f", index=False)
between_df.to_csv(export_fname2, na_rep="NA", float_format="%.4f", index=False)