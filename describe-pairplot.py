"""Draw a big correlation matrix of a bunch participant-level variables.
Correlations are run (when both variables are continous) and marked
in black if signficant, light gray otherwise.

The goal of this visualization is to show:
    - the general dream characteristics of the sample (among other variables)
    - which variables -- dream characteristics in particular -- are related to each other

Give it time!!! This takes forever to save, especially the hires.
"""
import os
import numpy as np
import pandas as pd
from scipy import stats
import utils

import colorcet as cc
import matplotlib.pyplot as plt
utils.load_matplotlib_settings()


#### Choose export path.
data_dir = utils.Config.data_directory
export_fname = os.path.join(data_dir, "results", "describe-pairplot.png")


#### Load and manipulate data

df = utils.load_data("participants")

# some conversions for plotting histograms
df["subjectCondition"] = pd.Categorical(df["subjectCondition"],
    categories=["control", "sham", "active"], ordered=True)
df["appVersion"] = pd.Categorical(df["appVersion"], ordered=True)
df["subjectCondition"] = df["subjectCondition"].cat.codes.replace(-1, pd.NA)
df["appVersion"] = df["appVersion"].cat.codes.replace(-1, pd.NA)


#### Define parameters.
HIST_KWARGS = dict(density=True, histtype="step", clip_on=False,
    color="white", edgecolor="black", linewidth=.5)
HIST2D_KWARGS = dict(density=False,
    cmin=1, cmap=cc.cm.dimgray_r, edgecolor="black", linewidth=0)
VARIABLE_SET = {
    "LDF": dict(n_opts=8, label="LDs", ticklabels=["0", "7+"]),
    "LDF-momentary": dict(n_opts=8, label="momentary\nLDs", ticklabels=["0", "7+"]),
    "LDF-prolonged": dict(n_opts=8, label="prolonged\nLDs", ticklabels=["0", "7+"]),
    "LDF-spontaneous": dict(n_opts=8, label="spontaneous\nLDs", ticklabels=["0", "7+"]),
    "LDF-deliberate": dict(n_opts=8, label="deliberate\nLDs", ticklabels=["0", "7+"]),
    "LDF-deliberateAttempts": dict(n_opts=8, label="deliberate\nLD attempts", ticklabels=["0", "7+"]),
    "LUSK": dict(n_opts=5, label="LD control\nrate", ticklabels=["none", "all"]),
    "avgAwakeLength": dict(n_opts=5, label="time awake", ticklabels=["0", "1 hr"]),
    "avgSleepQuality": dict(n_opts=5, label="sleep quality", ticklabels=["poor", "good"]),
    "subjectCondition": dict(n_opts=3, label="weekly cue\ncondition", ticklabels=["control", "active"]),
    "age": dict(n_opts=100, label="age", ticklabels=["young", "old"]),
    "appVersion": dict(label="app version", n_opts=df["appVersion"].nunique(), ticklabels=["early", "recent"]),
    "useFinishedApp": dict(n_opts=3, label="interest in\nfinished app", ticklabels=["no", "yes"]),
}

var_order = list(VARIABLE_SET.keys())
n_vars = len(var_order)
figsize = (n_vars*.8, n_vars*.8)


#### Draw plot.

# open figure and axes
fig, axes = plt.subplots(ncols=n_vars, nrows=n_vars,
    figsize=figsize, sharex=False, sharey=False)

# loop over rows and columns to plot each axis
for r in range(n_vars):
    for c in range(n_vars):
        ax = axes[r, c]
        ax.set_box_aspect(1)
        xvar = var_order[c]
        yvar = var_order[r]
        ax.grid(False)
        ax.tick_params(which="both", left=False, bottom=False, top=False, right=False)

        # choose bins and tick stuff
        if xvar == "age":
            xbins = np.linspace(-.5, VARIABLE_SET[xvar]["n_opts"]+.5, 20)
        else:
            xbins = np.arange(-.5, VARIABLE_SET[xvar]["n_opts"]+.5)
        if yvar == "age":
            ybins = np.linspace(-.5, VARIABLE_SET[yvar]["n_opts"]+.5, 20)
        else:
            ybins = np.arange(-.5, VARIABLE_SET[yvar]["n_opts"]+.5)
        xlim = (xbins[0], xbins[-1])
        ylim = (ybins[0], ybins[-1])
        xminorlocator = plt.MultipleLocator(1)
        yminorlocator = plt.MultipleLocator(1)
        xmajorlocator = plt.FixedLocator([0, VARIABLE_SET[xvar]["n_opts"]-1])
        ymajorlocator = plt.FixedLocator([0, VARIABLE_SET[yvar]["n_opts"]-1])
        xticklabels = VARIABLE_SET[xvar]["ticklabels"]
        yticklabels = VARIABLE_SET[yvar]["ticklabels"]

        ## drawing section
        if c == r: # diagonal -- draw histogram of x-axis variable
            n, bins, patches = ax.hist(xvar, bins=xbins, data=df, **HIST_KWARGS)
            for side, spine in ax.spines.items():
                if side in ["top", "left", "right"]:
                    spine.set_visible(False)
            ax.tick_params(left=False, labelleft=False, top=False, right=False)
            if c+1 < n_vars:
                ax.tick_params(bottom=False, labelbottom=False)
            n = df[xvar].notna().sum()
            n_txt = fr"$n={n:.0f}$"
            ax.text(.95, .95, n_txt, transform=ax.transAxes, ha="right", va="top")

        elif r < c: # upper triangle -- draw nothing
            ax.axis("off")
        elif r > c: # lower triangle -- heatmap of x/y variables
            plot_df = df[[xvar, yvar]].dropna()
            n = len(plot_df)
            ax.hist2d(xvar, yvar, bins=(xbins, ybins), data=plot_df, **HIST2D_KWARGS)
            if c > 0:
                ax.tick_params(which="both", labelleft=False)
            
            try: # run correlation and show stats if possible
                x = plot_df[xvar].values
                y = plot_df[yvar].values
                rval, pval = stats.spearmanr(x, y)
                r_txt = fr"$r={rval:.2f}$"
                if abs(rval) > 0 and abs(rval) < 1:
                    r_txt = r_txt.replace("0", "", 1)
                sigchars = "*" * sum([ pval < x for x in (.05, .01, .001) ])
                r_txt = sigchars + r_txt
                txt_color = "black" if pval < .1 else "gainsboro"
                ax.text(.95, .05, r_txt, color=txt_color,
                    transform=ax.transAxes, ha="right", va="bottom")
            except:
                pass
            ax.set_ylim(*ylim)

        ax.xaxis.set(major_locator=xmajorlocator, minor_locator=xminorlocator)
        ax.yaxis.set(major_locator=ymajorlocator, minor_locator=yminorlocator)
        ax.set_xticklabels(xticklabels)
        ax.set_yticklabels(yticklabels)
        ax.set_xlim(*xlim)
        if c == 0:
            ax.set_ylabel(VARIABLE_SET[yvar]["label"], labelpad=1)
        if r+1 == n_vars:
            ax.set_xlabel(VARIABLE_SET[xvar]["label"], labelpad=1)
        else:
            ax.tick_params(which="both", labelbottom=False)

fig.align_labels()


#### Export figure.
plt.savefig(export_fname)
utils.save_hires_copies(export_fname)
plt.close()