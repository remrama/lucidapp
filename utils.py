"""A set of generally useful functions.
Most are used in multiple scripts.
"""

def load_config(as_object=True):
    """Loads the json configuration file.
    With as_object True, it gets returned as a namespace,
    otherwise a dictionary. Namespace allows it to be
    accessed like config.data_dir instead of config["data_dir"].
    """
    import json
    from types import SimpleNamespace
    with open("./config.json", "r", encoding="utf-8") as jsonfile:
        if as_object:
            config = json.load(jsonfile, object_hook=lambda d: SimpleNamespace(**d))
        else:
            config = json.load(jsonfile)
    return config

# Load in the configuration file so it can be
# accessed easily with utils.Config within scripts.
Config = load_config()

import os
import logging
log_filename = os.path.join(Config.data_directory, "analysis.log")
logging.basicConfig(filename=log_filename,
    encoding="utf-8", level=logging.DEBUG,
    format="%(levelname)-8s :: %(asctime)s :: %(filename)s :: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")

def load_data(which):
    import os
    import pandas as pd
    data_dir = Config.data_directory
    trial_fname = os.path.join(data_dir, "derivatives", "trials-clean.csv")
    subject_fname = os.path.join(data_dir, "derivatives", "subjects-clean.csv")
    if which == "trials":
        return pd.read_csv(trial_fname)
    elif which == "subjects":
        return pd.read_csv(subject_fname)
    elif which == "merged":
        trial_df = pd.read_csv(trial_fname)
        subject_df = pd.read_csv(subject_fname)
        merged_df = trial_df.merge(subject_df, on="subjectID")
        return merged_df.reset_index(drop=False)
    else:
        raise ValueError(f"Unexpected value of {which} for which.")


def convert2ampm(string):
    # https://stackoverflow.com/a/54511526
    return string.replace("a.m.", "AM"
        ).replace("am", "AM"
        ).replace("pm", "PM"
        ).replace("p.m.", "PM"
        ).replace("a. m.", "PM"
        ).replace("p. m.", "PM"
        ).replace("de.", "?M"       ### ???? ###
        ).replace("du.", "?M"       ### ???? ###
        ).replace("nachm.", "PM"    # german
        ).replace("vorm.", "AM"     # german
        ).replace("ip.", "PM"       # finnish
        ).replace("ap.", "AM"       # finnish
        ).replace("da manhã", "AM"  # portuguese
        ).replace("da tarde", "PM"  # portuguese
        ).replace("fm", "AM"        # swedish
        ).replace("em", "PM"        # swedish
        ).replace("p.µ.", "AM"      # greek
        ).replace("µ.µ.", "PM"      # greek
        ).replace("??", "?M")       ### ???? ###



##################################### Plotting utils

def load_matplotlib_settings():
    """Load aesthetics I like.
    """
    from matplotlib.pyplot import rcParams
    # rcParams["figure.dpi"] = 600
    rcParams["savefig.dpi"] = 600
    rcParams["interactive"] = True
    rcParams["figure.constrained_layout.use"] = True
    rcParams["font.family"] = "Times New Roman"
    # rcParams["font.sans-serif"] = "Arial"
    rcParams["mathtext.fontset"] = "custom"
    rcParams["mathtext.rm"] = "Times New Roman"
    rcParams["mathtext.cal"] = "Times New Roman"
    rcParams["mathtext.it"] = "Times New Roman:italic"
    rcParams["mathtext.bf"] = "Times New Roman:bold"
    rcParams["font.size"] = 8
    rcParams["axes.titlesize"] = 8
    rcParams["axes.labelsize"] = 8
    rcParams["axes.labelsize"] = 8
    rcParams["xtick.labelsize"] = 8
    rcParams["ytick.labelsize"] = 8
    rcParams["axes.linewidth"] = 0.8 # edge line width
    rcParams["axes.axisbelow"] = True
    rcParams["axes.grid"] = True
    rcParams["axes.grid.axis"] = "y"
    rcParams["axes.grid.which"] = "major"
    rcParams["axes.labelpad"] = 2
    rcParams["xtick.top"] = True
    rcParams["ytick.right"] = True
    rcParams["xtick.direction"] = "in"
    rcParams["ytick.direction"] = "in"
    rcParams["grid.color"] = "gainsboro"
    rcParams["grid.linewidth"] = 1
    rcParams["grid.alpha"] = 1
    rcParams["legend.frameon"] = False
    rcParams["legend.edgecolor"] = "black"
    rcParams["legend.fontsize"] = 8
    rcParams["legend.title_fontsize"] = 8
    rcParams["legend.borderpad"] = 0
    rcParams["legend.labelspacing"] = .2 # the vertical space between the legend entries
    rcParams["legend.handlelength"] = 2 # the length of the legend lines
    rcParams["legend.handleheight"] = .7 # the height of the legend handle
    rcParams["legend.handletextpad"] = .2 # the space between the legend line and legend text
    rcParams["legend.borderaxespad"] = .5 # the border between the axes and legend edge
    rcParams["legend.columnspacing"] = 1 # the space between the legend line and legend text
    rcParams["hatch.linewidth"] = .3


def no_leading_zeros(x, pos):
    """A custom tick formatter for matplotlib
    that will remove leading zeros in front of decimals.
    """
    val_str = "{:g}".format(x)
    if abs(x) > 0 and abs(x) < 1:
        return val_str.replace("0", "", 1)
    else:
        return val_str


def save_hires_copies(png_fname, formats=["pdf"]):
    """Saves out hi-resolution matplotlib figures.
    Assumes there is a "hires" subdirectory within the path
    of the filename passed in, which must be also be a png filename.
    """
    import os
    from matplotlib.pyplot import savefig
    assert png_fname.endswith(".png"), f"Must pass a .png filename, you passed {png_fname}"
    png_dir, png_bname = os.path.split(png_fname)
    hires_dir = os.path.join(png_dir, "hires")
    for f in formats:
        ext = "." + f
        hires_bname = png_bname.replace(".png", ext)
        hires_fname = os.path.join(hires_dir, hires_bname)
        savefig(hires_fname)
