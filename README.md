# lucidapp

Analysis code for a project attempting to induce lucid dreams with a custom app.

**One comment about notation used in all the code files.** Each participant could use the app multiple times, and then could wakeup and fill out a dream report multiple times for each use. To stay consistent with the broader "participant/session/trial" language -- among other reasons -- a `session` refers to a single use of the app (typically a single night, but could be a nap) and a `trial` refers to a single dream report from within that `session` (typically one trial at the end of a session, but could wake up at multiple points and return to sleep).

- `participant` - app user
- `session` - sleep session, overnight or nap
- `trial` - awakening and dream report


## Code and file descriptions

This analysis requires the following files to exist already:
- `<data>/source/luciddreamdata.txt` - the raw Android app output
- `<data>/source/reports-4ratings.xls` - the experimenter dream report ratings
- `<data>/source/variables_legend.xlsx` - experimenter-generated file that holds info about all the variables in raw output

Where the location of the `<data>` directory is specified in the `config.json` configuration file.

All data files can be found on the [OSF project page](https://osf.io/tyc9w/).

For the `<data>/source/reports-4ratings.xls` file, an experimenter coded each dream report as falling into one of these categories:
- `lucid`
- `semi-lucid`
- `non-lucid`
- `white` - "I definitely had dreams, but do not remember them."
- `no recall` - Including none, nothing to report, no dreams, I did not dream, NA, etc.
- `no sleep` - Reported that they hadn't slept /fallen asleep yet.
- `not enough info` - When all information is completely unrelated to dreaming/sleeping (including random characters).
- `not english`


### Non-linear files

* `config.json` is where constants like the data directory are specified.
* `utils.py` is where generally useful python functions are stored.


### Linear files


#### Prepping data

```bash
# Generate the results directory structure that all files expect.
# (raw data should already be in data/source)
python setup-directories.py         #=> data/derivatives/
                                    #=> data/results/
                                    #=> data/results/hires/

# Go from raw json/txt data to csv. (It'll still be messy though.)
# Saves separate files for user data, dream report data, and app event data.
python setup-source2csv.py          #=> data/derivatives/participants.csv
                                    #=> data/derivatives/trials.csv
                                    #=> data/derivatives/events.json
                                    #=> data/derivatives/motion.json

###### ------------------------------------------------- ######
###### Manual step where someone coded the dream reports ######
###### ------------------------------------------------- ######

# Merge all the data into one file.
python setup-merge+clean.py         #=> data/derivatives/trials-clean.csv
                                    #=> data/derivatives/participants-clean.csv
```


#### Describing data

```bash
# Export some images that characterize the dataset.
python describe-samplesize.py       #=> data/results/samplesize.png
python describe-demographics.py     #=> data/results/demographics.png
python describe-correlations.py     #=> data/results/correlations.png
```


#### Analyzing data

```bash
# Test for an overall increase in LD rates with app use.
# Looks across all reports and all sessions (for those who have all 7).
python analyze-app_effect.py        #=> data/results/app_effect-data.csv
                                    #=> data/results/app_effect-descriptives.csv
                                    #=> data/results/app_effect-stats.csv
python plot-app_effect.py           #=> data/results/app_effect-plot.png

# Test if the cue had an impact on induction success.
# Looks across conditions for the first 2 sessions.
python analyze-cue_effect.py        #=> data/results/cue_effect-data.csv
                                    #=> data/results/cue_effect-descriptives.csv
                                    #=> data/results/cue_effect-stats_within.csv
                                    #=> data/results/cue_effect-stats_between.csv
python plot-cue_effect.py           #=> data/results/cue_effect-plot.png
```

**Note you can run all this at once with `runall.py`**