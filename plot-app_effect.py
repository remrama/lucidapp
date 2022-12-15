"""Graph dr.
"""
import os
import numpy as np
import pandas as pd

import utils

import matplotlib.pyplot as plt
utils.load_matplotlib_settings()


#### Choose import/export paths.
import_fname_data = os.path.join(utils.Config.data_directory, "results", "app_effect-data.csv")
import_fname_stats = os.path.join(utils.Config.data_directory, "results", "app_effect-stats.csv")
export_fname = os.path.join(utils.Config.data_directory, "results", "app_effect-plot.png")


#### Load data.
data = pd.read_csv(import_fname_data)
stats = pd.read_csv(import_fname_stats)

#### Define parameters.
FIGSIZE = (2.5, 2)
BAR_KWARGS = dict(width=.8, linewidth=1,
    color="gainsboro", edgecolor="black",
    error_kw=dict(linewidth=0.5, capsize=0))
DOT_KWARGS = dict(linewidth=0.5, color="black",
    ms=4, mec="black", marker="o", mew=0.5, mfc="gainsboro",
    elinewidth=.5, capsize=0, ecolor="black")

#### Extract data to plot.
xticks = np.array([-1, 1, 2, 3, 4, 5, 6, 7])
xticklabels = ["0\n(Prior 7 days)", "1", "2", "3", "4", "5", "6", "7"]
bar_xvals = xticks[[0, -1]]
bar_yvals = data[["baseline", "app"]].mean()
bar_evals = data[["baseline", "app"]].sem()
dot_xvals = xticks[1:]
dot_yvals = data[["1", "2", "3", "4", "5", "6", "app"]].mean()
dot_evals = data[["1", "2", "3", "4", "5", "6", "app"]].sem()

#### Draw bargraph.

# open figure
fig, ax = plt.subplots(figsize=FIGSIZE)

# draw bars and errorbars
bars = ax.bar(bar_xvals, bar_yvals, yerr=bar_evals, **BAR_KWARGS)

# draw dots and errorbars
ax.errorbar(dot_xvals, dot_yvals, yerr=dot_evals, **DOT_KWARGS)

# aesthetics
ylabel = "Total number of LDs\nper participant"
ax.set_ylabel(ylabel, labelpad=4)
# ax.set_xlim(min(xvals)-1, max(xvals)+1)
ax.margins(0.1)
ax.set_xticks(xticks)
ax.set_xticklabels(xticklabels)
ax.set_ylim(0, 1.5)
ax.set_xlabel("Number of days app used")
ax.grid(True, axis="y", which="major", clip_on=False)
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(axis="both", which="both", direction="out", top=False, right=False)
ax.yaxis.set_major_locator(plt.MultipleLocator(0.5))
ax.yaxis.set_minor_locator(plt.MultipleLocator(0.1))


#### Draw significance markers.

def draw_sig_bar(ax, xleft, xright, yloc, pchars, bheight=.01):
    # put buffers on the left/right to prevent overlap (clunky)
    xleft += .1
    xright -= .1
    barx = [xleft, xleft, xright, xright]
    bary = [yloc, yloc+bheight, yloc+bheight, yloc]
    if pchars:
        color = "black"
        mid = (xleft+xright)/2
        ax.text(mid, yloc, pchars, ha="center", va="bottom",
            transform=ax.get_xaxis_transform(), fontsize=10)
    else:
        color = "gainsboro"
    ax.plot(barx, bary, color=color, linewidth=1, transform=ax.get_xaxis_transform())

yloc = 0.8
pval = stats.loc[0, "p-val"]
asterisks = "*" * sum([ pval < cutoff for cutoff in (.05, .01, .001) ])
if not asterisks and pval < .1:
    asterisks = "~"
draw_sig_bar(ax, bar_xvals[0], bar_xvals[1], yloc, asterisks)


#### Export
plt.savefig(export_fname)
utils.save_hires_copies(export_fname)
plt.close()