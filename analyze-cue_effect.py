"""Test whether the cue increased LDs
by comparing lucidity across conditions for the first few nights.
"""
import os
import itertools
import numpy as np
import pandas as pd
import pingouin as pg

import utils



#### Choose export paths.

basename = "cue_effect"
export_dir = os.path.join(utils.Config.data_directory, "results")

export_fname_data = os.path.join(export_dir, f"{basename}-data.csv")
export_fname_descr = os.path.join(export_dir, f"{basename}-descriptives.csv")
export_fname_stats_within = os.path.join(export_dir, f"{basename}-stats_within.csv")
export_fname_stats_between = os.path.join(export_dir, f"{basename}-stats_between.csv")
# export_fname_plot = os.path.join(export_dir, f"{basename}-plot.csv")



################################# Load and wrangle data.

df = utils.load_data("merged")

# Remove dream reports that are "junk".
df = df[df["experimenterRating"].isin(["white", "non-lucid", "semi-lucid", "lucid"])]

# There might be a few dreams without a lucidity rating.
df = df.dropna(subset=["lucidSelfRating"])

# Convert boolean lucid success column to integer (1s/0s) for later math.
df["lucidSelfRating"] = df["lucidSelfRating"].astype(int)

# Most sessions have one trial, but some need to be aggregated into a single score.
# Sum the number of LDs for each session.
data = df.groupby(["subjectCondition", "subjectID", "sessionID"], as_index=False
    )["lucidSelfRating"].agg("sum")

# Reduce number of LDs to simple yes/no (1/0) lucidity. (doesn't change much, only a few have >1)
data["lucidSelfRating"] = data["lucidSelfRating"].ge(1).astype(int)

# Reduce to first 2 sessions (dropping anyone without both).
data = data[data["sessionID"].isin([1,2])]
data = data[data["subjectID"].duplicated(keep=False)]

# Get a single difference score for each participant
# that represents their change from session 1 -> session 2.
data = data.pivot(columns="sessionID", values="lucidSelfRating",
        index=["subjectCondition", "subjectID"]
    ).diff(axis=1)[2].rename("sessionChange"
    ).reset_index(drop=False)

descriptives = data.groupby("subjectCondition"
    )["sessionChange"].agg(["count", "mean", "sem"])





################# Run statistics.

### Within-condition effects
### (Do LD rates change from 1->2 within each condition?)

# ## Cochran/anova version
# stats_list = []
# for c, c_data in data.groupby("subjectCondition"):
#     c_stats = pg.cochran(data=c_data, dv="lucidSelfRating", within="sessionID", subject="subjectID")
#     c_stats.insert(0, "condition", c)
#     stats_list.append(c_stats)
# stats_within = pd.concat(stats_list)

# ## Wilcoxon/ttest version
# # !!! Sample too small
# stats = pg.pairwise_ttests(data=data, between="subjectCondition",
#     within="sessionID", dv="lucidSelfRating", subject="subjectID",
#     within_first=False, parametric=False).loc[4:]

## Bootstrap version
def pval_from_distribution(dist):
    pct_below = np.mean(dist < 0)
    pct_above = np.mean(dist > 0)
    min_pct = np.min([pct_below, pct_above])
    pval = 2 * min_pct
    return pval

stats_list = []
distributions = {} # for later between stats
for c, ser in data.groupby("subjectCondition")["sessionChange"]:
    ci, distr = pg.compute_bootci(ser.values,
        seed=0,
        func="mean", n_boot=2000, decimals=2, return_dist=True)
    stats_list.append({
        "subjectCondition": c,
        "n": ser.size,
        "mean": np.mean(distr),
        "ci_lo": ci[0],
        "ci_hi": ci[1],
        "pval": pval_from_distribution(distr),
    })
    distributions[c] = distr
stats_within = pd.DataFrame(stats_list)


### Between-condition effects
### (Do LD rates change from 1->2 more or less across conditions?)

# ## Wilcoxon/ttest version
# stats_between = pg.pairwise_ttests(data=data, between="subjectCondition",
#     dv="sessionChange", subject="subjectID", parametric=False)

## Bootstrap version
stats_list = []
for c1, c2 in itertools.combinations(["active", "sham", "control"], 2):
    differences = distributions[c1] - distributions[c2]
    pval = pval_from_distribution(differences)
    stats_list.append({
        "conditionA": c1,
        "conditionB": c2,
        "pval": pval,
    })

stats_between = pd.DataFrame(stats_list)



########## Export everything.
data.to_csv(export_fname_data, index=False, na_rep="NA")
descriptives.to_csv(export_fname_descr, index=True, na_rep="NA", float_format="%.3f")
stats_within.to_csv(export_fname_stats_within, index=False, float_format="%.5f")
stats_between.to_csv(export_fname_stats_between, index=False, float_format="%.5f")
