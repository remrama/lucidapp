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
export_fname_potentialn = os.path.join(export_dir, f"{basename}-potentialn.txt")



################################# Load and wrangle data.

df = utils.load_data("merged")

# Preliminary q: how many participants used app for 2 nights (1 and 2)?
subset = df[df["sessionID"].isin([1,2])]
subset = subset[~subset.duplicated(subset=["subjectID", "sessionID"], keep="first")]
potential_n = subset["subjectID"].value_counts().loc[lambda x: x==2].index.size
potential_n = f"{potential_n} participants completed both sessions 1 and 2."
with open(export_fname_potentialn, "w", encoding="utf-8") as f:
    f.write(potential_n)

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

# Flip out to a table with the 2 sessions as columns
data = data.pivot(columns="sessionID", values="lucidSelfRating",
        index=["subjectCondition", "subjectID"]
    ).rename(columns={1: "session1", 2: "session2"})

# Get a single difference score for each participant
# that represents their change from session 1 -> session 2.
data["sessionChange"] = data["session2"] - data["session1"]

descriptives = data.groupby("subjectCondition",
    )[["session1", "session2", "sessionChange"]
    ].agg(["count", "mean", "std", "sem"]
    ).T.reset_index().rename(columns={"level_1": "stat"})



################# Run statistics.

def pval_from_distribution(dist):
    pct_below = np.mean(dist < 0)
    pct_above = np.mean(dist > 0)
    min_pct = np.min([pct_below, pct_above])
    pval = 2 * min_pct
    return pval

### Within-condition effects
### (Do LD rates change from 1->2 within each condition?)

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
descriptives.to_csv(export_fname_descr, index=False, na_rep="NA", float_format="%.3f")
stats_within.to_csv(export_fname_stats_within, index=False, float_format="%.5f")
stats_between.to_csv(export_fname_stats_between, index=False, float_format="%.5f")
