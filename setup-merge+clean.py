"""Merge all 3 data files (user info, dream report info, and dream report ratings)
into 2 simplified files, one for all trials/dreams and one for users/participants.
And apply exclusion criteria (not based on stats, but just extra rows in the raw file).

1. Merge participants, sessions, trials, and ratings (and check things).
2. Exclude OBVIOUS stuff but save other exclusions for analysis file.
3. Export 2 files:
    - trials-clean.csv holding one row per trial/awakening/dream
    - participants-clean.csv holding one row per participant
"""
import os
import ast
import time
import string
import pandas as pd
import utils


##### Choose import/export paths.

import_fname_trials = os.path.join(utils.Config.data_directory, "derivatives", "trials.csv")
import_fname_participants = os.path.join(utils.Config.data_directory, "derivatives", "participants.csv")
import_fname_legend = os.path.join(utils.Config.data_directory, "source", "variables_legend.xlsx")
import_fname_ratings = os.path.join(utils.Config.data_directory, "source", "reports-4ratings.xls")

export_fname_trials = import_fname_trials.replace(".csv", "-clean.csv")
export_fname_participants = import_fname_participants.replace(".csv", "-clean.csv")


##### Load data.

trial_df = pd.read_csv(import_fname_trials)
participant_df = pd.read_csv(import_fname_participants)
trial_legend = pd.read_excel(import_fname_legend, sheet_name="trials")
participant_legend = pd.read_excel(import_fname_legend, sheet_name="participants")
assert trial_df.shape[1] == trial_legend.shape[0]
assert participant_df.shape[1] == participant_legend.shape[0]

ratings_df = pd.read_excel(import_fname_ratings,
    names=["subjectID", "timestampOrig", "dreamReport", "experimenterRating"])

# Reduce items in legends to only the relevant ones.
trial_legend = trial_legend.query("keep")
participant_legend = participant_legend.query("keep")



##### Make some convenience functions that'll be used later.

def convert2ts(string, orig_fmt, new_fmt):
    """Convert a raw string timestamp to ISO-formatted string."""
    if pd.isna(string):
        return pd.NA
    # Replace non-english AM/PM
    time_str = utils.convert2ampm(string)
    if "?" in time_str:
        return pd.NA
    else:
        # Convert to ISO format.
        tstamp_obj = time.strptime(time_str, orig_fmt)
        tstamp_str = time.strftime(new_fmt, tstamp_obj)
        return tstamp_str



##### Make functions that do heavy-lifting,
##### since most of these steps need to be
##### applied to multiple dataframes.

def clean_ratings_file(df_):
    """Clean the ratings files a bit.
    """
    df = df_.copy()

    # Correct for some weird thing about reading/saving excel files.
    df["subjectID"] = df["subjectID"].astype(str)

    # Fix typos of trailing spaces and replace nans bc they're supposed to be "null".
    df["experimenterRating"] = df["experimenterRating"].str.strip().fillna("not enough info")

    # Drop the dream report column since it will be redundant with column from other file.
    df = df.drop(columns="dreamReport")

    return df


def reduce_dataframe(df, legend):
    """Use the variables_legend file to reduce the raw file
    down to variables of interest.
    """
    # Reorder columns according to legend excel sheet.
    # Rename them according to the values in legend excel sheet.
    df = df.reindex(columns=legend["variable"]
        ).rename(columns=legend.set_index("variable")["shortname"]
        ).rename_axis(columns=None)
    # Just as in the user dataframe, participants 548785739 and 93689039
    # have some full row duplicates, so remove them.
    # **Do this before converting timestamps, bc this is how it was done to export the file for report ratings.
    df = df.drop_duplicates(keep="first", ignore_index=True)
    # Keep the original timestamp column because it's an
    # identifier in the manually coded dream reports file.
    if "timeStart" in legend["shortname"].values:
        timestamp_orig = df["timeStart"].copy()
        df.insert(df.columns.tolist().index("timeStart"), "timestampOrig", timestamp_orig)
    return df


##### Convert wakeup time to a proper timestamp

def adjust_column_values(df_, legend):
    df = df_.copy()
    for shortname, row in legend.set_index("shortname").iterrows():
        if row["type"] in ["mixed", "string"]:
            continue
        elif row["type"] == "integer":
            df[shortname] = df[shortname].astype("Int64")
        elif row["type"] == "float":
            df[shortname] = df[shortname].astype(float)
        elif row["type"] == "boolean":
            bool_values = ast.literal_eval(row["values"])
            assert len(bool_values) == 2
            replacements = { k: v for k, v in zip(bool_values, [True, False])}
            df[shortname] = df[shortname].replace(replacements).astype("boolean")
        elif row["type"] in ["ordinal", "nominal"]:
            ordered = row["type"]=="ordinal"
            categories = ast.literal_eval(row["values"])
            categorical = pd.Categorical(df[shortname], categories=categories, ordered=ordered)
            assert categorical.isna().sum() == df[shortname].isna().sum(), f"Categories in {shortname} might be inaccurate!!"
            df[shortname] = categorical
            if row["type"] == "ordinal":
                df[shortname] = df[shortname].cat.codes.replace(-1, pd.NA)
        elif row["type"] == "datetime":
            NEW_FORMAT = "%Y-%m-%dT%H:%M:%S"
            old_format = row["values"]
            df[shortname] = df[shortname].apply(convert2ts, orig_fmt=old_format, new_fmt=NEW_FORMAT)
        else:
            raise ValueError(f"Unexpected variable type!!")
    return df


def clean_trials_dataframe(df_):
    df = df_.copy()

    ## The four different columns asking about how cues appeared in dreams
    ## seem to be non-overlapping, so probably all the same thing and can
    ## merge them into one column.
    # Make sure they are nonoverlapping by checking that
    # there is never more than 1 NOT null in a row.
    how_cues_appeared_start = "reportHowCuesAppeared"
    cue_in_dream_columns = [ c for c in df.columns if c.startswith(how_cues_appeared_start) ]
    assert df[cue_in_dream_columns].notna().sum(axis=1).le(1).all(), "Expected non-overlapping."
    how_cues_appeared = df[cue_in_dream_columns[0]
        ].fillna(df[cue_in_dream_columns[1]]
        ).fillna(df[cue_in_dream_columns[2]]
        ).fillna(df[cue_in_dream_columns[3]])
    df.insert(df.columns.tolist().index(cue_in_dream_columns[0]), how_cues_appeared_start, how_cues_appeared)
    df = df.drop(columns=cue_in_dream_columns)

    ########### combine LuCiD scores
    LuCiD_columns = [ c for c in df if c.startswith("LuCiD") ]
    if LuCiD_columns:
        LuCiD_scores = df[LuCiD_columns].mean(axis=1).round(1)
        df.insert(df.columns.tolist().index(LuCiD_columns[0]), "LuCiD", LuCiD_scores)
        df = df.drop(columns=LuCiD_columns)

    ########### Add trial ID
    # Sort by participant, and by time within each participant.
    df = df.sort_values(["subjectID", "sessionID", "timeStart"])
    # Add trial ID, indicating number of trials (ie, awakenings) within each night (ie, session).
    # (timeStart column is selected arbitrarily)
    trial_id =  df.groupby(["subjectID", "sessionID"]
        )["timeStart"].transform(lambda s: range(1, 1+s.size)
        ).astype("Int64")
    df.insert(2, "trialID", trial_id)

    # # We have experimentalNight for the night so replace 11-13
    # df["condition"] = df["condition"].replace({11:1, 12:2, 13:3})
    # # Replace these with what I suspect are right and check.
    # df["cueCondition"] = df["cueCondition"].replace({1:"active", 2:"sham", 3:"control"})
    # # df["currentCueMode"] = df["currentCueMode"].replace({1:"sham", 2:"active", 3:"control"})
    return df


def clean_participants_dataframe(df_):
    df = df_.copy()
    lusk_columns = [ c for c in df if c.startswith("LUSK") ]
    if lusk_columns:
        lusk_scores = df[lusk_columns].mean(axis=1).round(1)
        df.insert(df.columns.tolist().index(lusk_columns[0]), "LUSK", lusk_scores)
        df = df.drop(columns=lusk_columns)
    df = df.sort_values("subjectID")
    return df


trial_df = reduce_dataframe(trial_df, trial_legend)
participant_df = reduce_dataframe(participant_df, participant_legend)

trial_df = adjust_column_values(trial_df, trial_legend)
participant_df = adjust_column_values(participant_df, participant_legend)

trial_df = clean_trials_dataframe(trial_df)
participant_df = clean_participants_dataframe(participant_df)
ratings_df = clean_ratings_file(ratings_df)


############### Merge the ratings with the reports.

# These two dataframes are supposed to be match on participant and timestamp.
# The ratings file was resaved as excel so it messed with some special characters
# at the end of timestamps. Cut them off, make sure everything is still unique
# and that all the ratings match something in the reports file.
trial_df["timestampCut"] = trial_df["timestampOrig"].str[:19]
ratings_df["timestampCut"] = ratings_df["timestampOrig"].str[:19]
trial_uniqs = trial_df.groupby(["subjectID", "timestampCut"]).size()
rating_uniqs = ratings_df.groupby(["subjectID", "timestampCut"]).size()
assert trial_uniqs.eq(1).all()
assert rating_uniqs.eq(1).all()
assert all([ x in trial_uniqs.index for x in rating_uniqs.index ])

# **Keep the many rows from report dataframe that were not included in the ratings.
# remove the timestamps and dreamreport columns which are unneeded now
# set indices for proper concatenation
trial_df = trial_df.set_index(["subjectID", "timestampCut"]).drop(columns="timestampOrig")
ratings_df = ratings_df.set_index(["subjectID", "timestampCut"]).drop(columns="timestampOrig")

trial_df = pd.concat([trial_df, ratings_df], axis=1,
        verify_integrity=True, join="outer"
    ).droplevel("timestampCut").reset_index(drop=False)


# trial_df = trial_df.drop(columns=["timestampOrig", "timestampOrigCut"])

# df = pd.merge(
#     trial_df, ratings_df[["subjectID", "timestampCut", "dreamReportType"]],
#     on=["subjectID", "timestampCut"], how="left", validate="1:1")
# # Remove the unformatted timestamps.
# df = df.drop(columns=["timestampOrig", "timestampOrigCut"])




############################# Dropping participants.

##### Reduce the participants file down to participants in final dataset.

## There are WAY more participants in the participants file than trials file.
## Likely since people signed up for the app and then didn't use the app.

# Make sure every participant in trials file is in participant file.
assert participant_df["subjectID"].is_unique, "Expected a unique participant in each row, one or more duplicates present."
assert trial_df["subjectID"].isin(participant_df["subjectID"]).all()

# Remove anybody from participant file not in trial file.
participant_df = participant_df[participant_df["subjectID"].isin(trial_df["subjectID"])]

# Remove anyone under 18
participant_df = participant_df[participant_df["age"]>=18]
utils.logging.info("Removing one participant reporting age of 90000.")
participant_df = participant_df[participant_df["age"].ne(90000)]

# Remove early app versions.
MINIMUM_APP_VERSION = 63
# First drop any a/b/etc off the app version
participant_df = participant_df[
        participant_df["appVersion"].map( # 
            lambda x: pd.NA if pd.isna(x) else float("".join([ c for c in x if c.isdigit() ]))
        ).ge(MINIMUM_APP_VERSION)
    ]

# Almost all participants are a long number.
# Others are nathan, nb, Kaj, Sandra, alalalala,
# and then about 20 4-character codes like c235 (all one letter three numbers).
# I assume those are pilots or something, so taking them out.
#
# **Note this is NOT true for the user dataframe. But there are
# far more participants in the user dataframe than reports dataframe.
participant_df = participant_df[participant_df["subjectID"].str.isdigit()]


### Reduce to only these participants in the trials file
### and see where that gets you.
trial_df = trial_df[trial_df["subjectID"].isin(participant_df["subjectID"])]


#################### Exclude nights beyond night 7 and those without info.

# trial_df = trial_df[trial_df["sessionID"].notna()]
trial_df = trial_df[trial_df["sessionID"].le(7)]
trial_df["sessionID"] = trial_df["sessionID"].astype(int)

# Since this might have taken some participants out of the trials file,
# need to make sure the participants file gets reduced to only those in trial file.
participant_df = participant_df[participant_df["subjectID"].isin(trial_df["subjectID"])]


# # Convert participant IDs to integers
# trial_df["subjectID"] = trial_df["subjectID"].astype(int)
# participant_df["subjectID"] = participant_df["subjectID"].astype(int)
# Convert participant ID to letters so it's obv categorical.
num2alpha = lambda num: "".join([ string.ascii_uppercase[int(dig)] for dig in str(num) ])
trial_df["subjectID"] = trial_df["subjectID"].map(num2alpha)
participant_df["subjectID"] = participant_df["subjectID"].map(num2alpha)


############### Check the necessary columns are filled
# CRITICAL_COLUMNS = ["subjectID", "sessionID", "trialID",
#     "experimentNight",
#     "nightCondition"]
# df = df[df[CRITICAL_COLUMNS].isnull().any(axis=1).eq(False)]


# Export.
trial_df.to_csv(export_fname_trials, index=False, na_rep="NA")
participant_df.to_csv(export_fname_participants, index=False, na_rep="NA")
