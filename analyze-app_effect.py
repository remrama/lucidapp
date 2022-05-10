"""Test whether the app increased LDs
by comparing a 7-session total against a baseline week.
"""
import os
import numpy as np
import pingouin as pg

import utils



#### Choose export paths.

basename = "app_effect"
export_dir = os.path.join(utils.Config.data_directory, "results")

export_fname_data = os.path.join(export_dir, f"{basename}-data.csv")
# export_fname_descr = os.path.join(export_dir, f"{basename}-descriptives.csv")
export_fname_stats = os.path.join(export_dir, f"{basename}-stats.csv")
# export_fname_plot = os.path.join(export_dir, f"{basename}-plot.csv")



################################# Load and wrangle data.

df = utils.load_data("merged")

# There might be a few dreams without a lucidity rating.
df = df.dropna(subset=["lucidSelfRating"])

# Convert boolean lucid success column to integer (1s/0s) for later math.
df["lucidSelfRating"] = df["lucidSelfRating"].astype(int)

# Shouldn't be more than 7 sessions but just to be sure.
df = df[df["sessionID"].isin([1,2,3,4,5,6,7])]

# Most sessions have just one trial, but some need to be aggregated into a single score.
# Sum the number of LDs for each session.
session_df = df.groupby(["subjectID", "sessionID"], as_index=False
    )["lucidSelfRating"].agg("sum")

# Reduce number of LDs to simple yes/no (1/0) lucidity. (doesn't change much, only a few have >1)
session_df["lucidSelfRating"] = session_df["lucidSelfRating"].ge(1).astype(int)

# Pivot out to a table that has sessions as columns
table = session_df.pivot(columns="sessionID", values="lucidSelfRating", index="subjectID")

# Reduce to subjects with all 7 sessions
table = table[table.notna().all(axis=1)]

# Sum across all sessions to get cumulative total amount of LDs per participant per day.
cumtable = table.cumsum(axis=1)

# Get the baseline scores for each participant and merge with session data.
baseline = df[["subjectID","LDF"]].drop_duplicates("subjectID")
data = cumtable.merge(baseline, on="subjectID")

data = data.rename(columns={7: "app", "LDF": "baseline"})

# # Get descriptives summary for the cumulative version.
# cumtable_descr = totals[["all_sessions", "baseline"]
#     ].agg(["count", "mean"]).round(3).T.unstack(level=1)



####### Run statistics
a = data["baseline"].values
b = data["app"].values
stats = pg.wilcoxon(a, b)

stats.loc["Wilcoxon", "mean-n"] = len(a) # same as b
stats.loc["Wilcoxon", "mean-app"] = np.mean(b)
stats.loc["Wilcoxon", "mean-app"] = np.mean(b)


################## Export session-level data, descriptives, and stats.
data.to_csv(export_fname_data, index=True, na_rep="NA")
stats.to_csv(export_fname_stats, index=True, float_format="%.4f")
