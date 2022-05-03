"""Initialize the data directory structure used throughout the rest of the scripts.

Puts some new directories inside the "data directory"
specified in the <config.json> configuration file.

Subdirectory motivations are described briefly below.

Source data should already be in data/source!!
"""
import os
import utils

DATA_SUBDIRECTORIES = [
    "derivatives",      # for mid-stage, between source and results
    "results",          # for final output (plots, stats tables, etc.)
    "results/hires",    # for high resolution plots (vector graphics)
]

if not os.path.isdir(utils.Config.data_directory):
    os.mkdir(utils.Config.data_directory)

for subdir in DATA_SUBDIRECTORIES:
    subdir_path = os.path.join(utils.Config.data_directory, subdir)
    if not os.path.isdir(subdir_path):
        os.mkdir(subdir_path)
