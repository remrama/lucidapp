"""Convert raw android app data to user-friendly csv and json files.
The output is still uncleaned and unprocessed, in that
it needs to be followed up with a script to tidy it up.

Raw/source data from the app essentially a bunch of json files
on each line of a text file, but there are multiple formatting
issues -- like unbalanced quotes -- that prevent the use of a
simple json.load().

A further complication is that there are multiple versions
of the app, and the output from each doesn't match 100%.

This script attempts to parse it all out and export 3 files:
    - a "participants" **csv** file that has one user per row and relevant info
    - a "trials" **csv** file that has one dream report per row
    - a "events" **json** file with one entry per user and lots of timestamped events
    - a "motion" **json** file with one entry per user and lots of timestamped events
"""
import os
import re
import json
import pandas as pd

import utils


# This regex pattern is used to parse eventLog and motionData (see below).
TIMESTAMP_REGEX = r"([0-9]{2}-[0-9]{2}-[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2} [AP\?]M)"



####################### I/O filenames and load data.

data_dir = utils.Config.data_directory

import_fname = os.path.join(data_dir, "source", "luciddreamdata.txt")

export_fname_users = os.path.join(data_dir, "derivatives", "participants.csv")
export_fname_reports = os.path.join(data_dir, "derivatives", "trials.csv")
export_fname_events = os.path.join(data_dir, "derivatives", "events.json")
export_fname_motion = os.path.join(data_dir, "derivatives", "motion.json")

# Load source data as one big string.
with open(import_fname, "r", encoding="windows-1252") as infile:
    data = infile.read()



####################### Parse the raw data file.

## Split txt file into separate and meaningful lines.
##
## The data file is separated by newlines (ie, return characters).
## Each data takes up 2 consecutive rows, where the 1st row
## is just the participant ID and the 2nd row is a data entry.
## One row will have the participant ID, then the next row the data.
## There's also the occassional empty row, but those can be taken out.

# Break apart the txt file by splitting at each new line (ie, each return).
# This also inherently removes any empty lines.
content_lines = [ line for line in data.splitlines() if line ]

# Make sure there's an even number of lines (bc assuming lines are ID/data pairings).
assert len(content_lines)%2 == 0, "Expected even number of lines, found odd."
# Make sure each odd line has the phrase PARTICIPANT in it.
assert all([ "PARTICIPANT:" in l for l in content_lines[::2] ]), "Expected 'PARTICIPANT' to appear in all odd lines, it didn't."


## Loop over all lines and build lists of user data and dream report data.
##
## Each pair of lines is data from a participant.
## The tough part is parsing/extracting the data from
## each of those. Do that here, save to lists, and then
## later compile the lists into dataframes to export as csv.

# Initialize empty containers to store data while iterating.
# 2 empty lists to hold user and dream report data.
# 2 empty dictionaries for user event and motion data.
user_data_list = []
report_data_list = []
event_log_dict = {}
motion_log_dict = {}

# Loop over the odd and even elements of the lines list,
# which will be participant ID and all their data, respectively.
for participant_string, data_string in zip(content_lines[::2], content_lines[1::2]):

    # Extract the participant ID from the participant string
    # (ie, remove "PARTICIPANT:" off the left).
    participant_id = participant_string.split("PARTICIPANT:")[1]

    ## The variable <data_string> *LOOKS* like a json,
    ## but it's complicated because there are json formatting
    ## issues that prevent it from being loaded as-is.
    ##
    ## I think most of the issue comes from the dream report
    ## dictionaries/jsons buried in the larger data structure (also json).
    ##
    ## I think the best approach is to
    ##  (1) extract the dream reports for a separate dataframe
    ## and then
    ##  (2) remove them from the larger data string so that the
    ##      rest can be properly decoded without error.

    # Find all the dream reports in data_string.
    # - Look for "dreamReport".
    #   It often looks like this in context:
    #   33:15 vorm."}","dreamReport_03\\/10\\/2021
    # - It shouldn't follow "nextScreen" since in those cases it
    #   isn't actually a dream report, but just a button option?
    #   Instead of using a lookback (e.g., (?<!nextScreen":"))
    #   we can take only "dreamReport" following a comma.
    # - Use regex to capture everything following "dreamReport"
    #   until the next closing bracket, since that's the end of the dream data.
    dream_reports = re.findall(r',"dreamReport.*?\}', data_string)

    # There is one element in this list for every dream report found.
    # So if the list is empty, no dream reports were found.
    # If there are any dream reports, add them to the list of dream report data.
    if dream_reports: # This means there is >= 1 dream report.
        # Loop over each dream report entry from this participant.
        for dr in dream_reports:

            ## Parse apart the dream report data!
            ##
            ## Sometimes the dream report json is surrounded
            ## by quotes and other times it's not.
            ## This has to be handled in 2 separate areas.

            # Check if the dream report json is surrounded by quotes.
            data_quoted = False if '":{"' in dr else True # Sorry this is weirdly backwards.
            
            # Separate the timestamp and data.
            if data_quoted:
                tstamp_str, report_data_str = dr.split('":"', 1)
            else:
                tstamp_str, report_data_str = dr.split('":', 1)

            # Convert the timestamp string into real timestamp.
            time_str = tstamp_str.split("_", 1)[1] # Timestamp should occur after the first underscore.
            time_str = time_str.replace(r"\/", "-")
            # The timestamp will still look weird, but correct it in the cleaning script.

            # Load the dream report json as a dictionary! :))))))
            report_data = json.loads(report_data_str)

            # Add the participant ID and timestamp to the dream report dictionary.
            report_data["participant_id"] = participant_id
            report_data["timestamp"] = time_str

            # Save this dream report dictionary to the list, to put in dataframe later.
            report_data_list.append(report_data)

            ## We're done with parsing the dream report, but
            ## now it has to be removed from the overall data
            ## string so that the non-dream stuff (ie, user data)
            ## can be properly parsed down the road.

            # Remove this particular dream report string
            # from the whole dream report data string.
            if data_quoted:
                # If the json was surrounded by quotes, make sure we
                # get the closing quote out too, which wasn't in the original search.
                data_string = data_string.replace(dr+'"', "")
            else:
                # If not surrounded by quotes, take what was originally found.
                data_string = data_string.replace(dr, "")

    ## Now the goal is to parse out the rest of the
    ## remaining (non-dream) data into a user-info json.
    ##
    ## Before doing so, it has to be cleaned just a bit
    ## more to account for some weird cases that mess
    ## up json decoding (mostly about quotes again).

    # Find the instances where there is an extra double-quote
    # after the "recruitedFrom" because they were recruited from
    # some organization that has quotes in it (like "Publico" or "Quirks and Quarks").
    if 'participantRecruitedFrom":' in data_string:
        recruited_from = data_string.split('participantRecruitedFrom":',1)[1].split(',"')[0]
        if recruited_from.count('"') > 2:
            data_string = data_string.replace(recruited_from[1:-1], recruited_from.replace('"',"'"))
    # Participants can insert feedback, and participant ID 96471003
    # provides feedback that has quotes in it and mess up parsing.
    # It's an idiosyncratic case so remove the quotes.
    # ("the voice "finish the dream report" that appears if I writing my dream report too long is very annoying")
    if participant_id == "96471003":
        data_string = data_string.replace('"finish the dream report"', "finish the dream report")
    
    # Load the user data json as a dictionary.
    user_data = json.loads(data_string)

    # Participant ID appears twice. It was before in the dream data
    # and also here in the user data. Check that the two IDs match.
    # Will only be relevant if dream reports were saved. Also some
    # entries have no participant ID, eg some with just an app version.
    if dream_reports:
        assert participant_id == str(user_data["pid"]), "Expected two participant IDs to match, they didn't."

    ## Event and motion logs ("eventLog", "motionData") are massive
    ## and clutter up any csv export. They also require additional
    ## parsing. Here, parse them and save to separate dictionaries
    ## then remove from the user data before saving that to the running list.
    # Both eventLog and motionData can be parsed almost identically.
    # Both are split by timestamp and result in pairs of timestamp and data.
    # The cleaning up of "data" is only slightly different (see below).
    for logname in ["eventLog", "motionData"]:
        if logname in user_data:
            # Pop out the data.
            logdata = user_data.pop(logname)
            # To split by timestamp, need non-english AM/PM to be converted to AM/PM.
            logdata = utils.convert2ampm(logdata)
            # Split entries apart, which should then alternate timestamp/data like the user/data structure of main file.
            logentries = [ e.strip() for e in re.split(TIMESTAMP_REGEX, logdata) if e ]
            # Check that logentries exists and is divisible by 2,
            # since the entries should be in pairs of timestamp and info.
            assert logentries and len(logentries)%2 == 0, "Expected an even number of items, found odd or zero."
            # Create a dictionary of entries for this participant.
            if logname == "eventLog": # Remove colons from eventLog entries.
                entry_dict = { a: b.strip(":") for a, b in zip(logentries[::2], logentries[1::2]) }
            elif logname == "motionData": # Remove leading comma from motionData entries.
                entry_dict = { a: b[1:] for a, b in zip(logentries[::2], logentries[1::2]) }
            # Add to running dictionaries (use user_data version of participant ID).
            participant_id_user_version = str(user_data["pid"])
            if logname == "eventLog":
                if participant_id_user_version in event_log_dict:
                    msg = f"subj {participant_id_user_version} has a new {logname} log, overwriting previous..."
                    utils.logging.warning(msg)
                event_log_dict[participant_id_user_version] = entry_dict
            elif logname == "motionData":
                if participant_id_user_version in motion_log_dict:
                    msg = f"subj {participant_id_user_version} has a new {logname} log, overwriting previous..."
                    utils.logging.warning(msg)
                motion_log_dict[participant_id_user_version] = entry_dict

    # Save user dictionary the master list for later compiling into dataframe! :)
    user_data_list.append(user_data)



## Congratulations.
## All data has been parsed and can now be compiled into dataframes.

user_df = pd.DataFrame(user_data_list)
report_df = pd.DataFrame(report_data_list)


## Clean up the dataframes.
##
## Not preprocessing, but just clean enough to be manageable later.

# Replace any empty string cells with NaNs.
user_df = user_df.replace("", pd.NA)
report_df = report_df.replace("", pd.NA)

# The dream report dataframe has a column with an empty string
# as the column name, rename as UNNAMED explicitly.
report_df = report_df.rename(columns={"":"UNNAMED"})

# There are two pid columns but one has no information.
# "pid" is good, while " pid" (with a leading zero) is
# _almost_ empty. I only found one cell with data, marking
# " pid" as 505a. But the same 505a is in "pid" too, so
# that column can be dropped.
assert 1 == user_df[" pid"].notnull().sum(), "Expected one filled cell, found more or less than that."
assert "505a" == user_df[" pid"].dropna().unique()[0], "Expected 505a as the only filled cell, it was something else."
user_df = user_df.drop(columns=" pid")

# Both dataframes have some columns with leading spaces in the name.
# Replace them with non-leading-zero versions, but first makes sure
# that won't overwrite anything (as it would have for " pid" and "pid").
assert not any([ (c.strip() in user_df.columns and c.strip() != c ) for c in user_df.columns ]), "Stripping column names will cause duplicates."
assert not any([ (c.strip() in report_df.columns and c.strip() != c ) for c in report_df.columns ]), "Stripping column names will cause duplicates."
user_df.columns = user_df.columns.str.strip()
report_df.columns = report_df.columns.str.strip()

# The user dataframe has a *lot* of columns because of something
# where many user data dictionaries have a *unique* key because
# it includes a timestamp. For example
#   Enter wake-up time:11:18:00
#   Enter usual wake-up time:8:05:00 PM
#   Enter bedtime:03:00:00
#   Enter usual wake-up time:10 h 11 min 00 s
#   night7_Enter usual bedtime (Past week):10:48:00 AM
# These are not really meaningful so 
# remove them. Could just look for a colon ":", but to be safe
# also search for "Enter".
user_df = user_df.drop(columns=
    [ c for c in user_df.columns if (":" in c and "Enter" in c) ])



# Export everything!
user_df.to_csv(export_fname_users, index=False, na_rep="NA")
report_df.to_csv(export_fname_reports, index=False, na_rep="NA")
with open(export_fname_events, "w", encoding="utf-8") as outfile:
    json.dump(event_log_dict, outfile, indent=4, sort_keys=False, ensure_ascii=False)
with open(export_fname_motion, "w", encoding="utf-8") as outfile:
    json.dump(motion_log_dict, outfile, indent=4, sort_keys=False, ensure_ascii=False)