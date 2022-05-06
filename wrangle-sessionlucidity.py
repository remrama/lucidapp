"""Export a dataframe that aggregates lucidity scores within each session.
Include a separate output with descriptive summary statistics.

The output from here is used for main analyses.
"""
import os
import utils


#### Choose export path.
export_fname = os.path.join(utils.Config.data_directory, "derivatives", "session_lucidity.csv")
export_fname_summary = os.path.join(utils.Config.data_directory, "results", "session_lucidity.csv")


#### Load data.
df = utils.load_data("merged")


#### Wrangle data.

# Remove dream reports that are "junk".
df = df[df["experimenterRating"].isin(["white", "non-lucid", "semi-lucid", "lucid"])]

# There might be a few dreams without a lucidity rating.
df = df.dropna(subset=["lucidSelfRating"])

# Convert the boolean lucid success column to integer (1s/0s).
df["lucidSelfRating"] = df["lucidSelfRating"].astype(int)

# Pivot to a new dataframe with session-level scores (cells denote lucidity).
# Most sessions have one trial, but some need to be aggregated into a single score.
# Sum within session and then binarize.

# Sum the number of LDs for each session.
GROUPING_VARS = ["subjectCondition", "subjectID", "sessionID"]
session_df = df.groupby(GROUPING_VARS, as_index=False
    )["lucidSelfRating"].agg("sum")

# Reduce number of LDs to simple yes/no (1/0) lucidity.
# (doesn't change much, only a few have >1)
session_df["lucidSelfRating"] = session_df["lucidSelfRating"].ge(1).astype(int)

# Generate descriptive statistics for each condition/session combination.
session_summary = session_df.groupby(["subjectCondition", "sessionID"]
    )["lucidSelfRating"].agg(["count", "mean"]
    ).round(3)

session_df.to_csv(export_fname, index=False, na_rep="NA")
session_summary.to_csv(export_fname_summary, index=True, na_rep="NA")