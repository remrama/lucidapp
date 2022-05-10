"""Graph first session results.
"""
import os
import numpy as np
import pandas as pd

import utils

import matplotlib.pyplot as plt
utils.load_matplotlib_settings()


#### Choose import/export paths.
import_fname1 = os.path.join(utils.Config.data_directory, "results", "cue_effect-stats_within.csv")
import_fname2 = os.path.join(utils.Config.data_directory, "results", "cue_effect-stats_between.csv")
export_fname = os.path.join(utils.Config.data_directory, "results", "cue_effect-plot.png")


#### Load data.
within_df = pd.read_csv(import_fname1, index_col="subjectCondition")
between_df = pd.read_csv(import_fname2, index_col=["conditionA", "conditionB"])


#### Define parameters.
FIGSIZE = (2, 3)
BAR_KWARGS = dict(width=.8, linewidth=1, edgecolor="black",
    error_kw=dict(linewidth=.5, capsize=0))
CONDITION_ORDER = ["control", "sham", "active"]
HATCH_STYLES = {
    "control": "xx",
    "sham": "//",
    "active": None,
}
palette = utils.load_config(as_object=False)["colors"]
colors = [ palette[cond] for cond in CONDITION_ORDER ]
hatches = [ HATCH_STYLES[cond] for cond in CONDITION_ORDER ]


#### Extract data to plot.
xvals = np.arange(3)
yvals = within_df.loc[CONDITION_ORDER,"mean"]
lovals = within_df.loc[CONDITION_ORDER,"ci_lo"]
hivals = within_df.loc[CONDITION_ORDER,"ci_hi"]
evals = [np.abs(lovals-yvals), np.abs(hivals-yvals)]


#### Draw bargraph.

# open figure
fig, ax = plt.subplots(figsize=FIGSIZE)

# draw a line at zero
ax.axhline(0, color="black", linewidth=1, linestyle="solid")

# draw bars and errorbars
bars = ax.bar(xvals, yvals, yerr=evals, color=colors, hatch=hatches, **BAR_KWARGS)

# aesthetics
ylabel = r"Change in session $1\rightarrow2$ lucid frequency"
ax.set_ylabel(ylabel, labelpad=4)
ax.set_xlim(min(xvals)-1, max(xvals)+1)
ax.set_ylim(-.6, .6)
ax.grid(True, axis="y", which="both", clip_on=False)
for side, spine in ax.spines.items():
    if side != "left":
        spine.set_visible(False)
ax.tick_params(axis="both", which="both",
    labelbottom=False, top=False, right=False, bottom=False)
ax.yaxis.set(
    major_locator=plt.MultipleLocator(.2),
    major_formatter=plt.matplotlib.ticker.PercentFormatter(xmax=1)
)


#### Draw significance markers.

get_asterisks = lambda p: "*" * sum([ p < cutoff for cutoff in (.05, .01, .001) ])

# within conditions (individual bars)

for x, c in zip(xvals, CONDITION_ORDER):
    pval = within_df.loc[c, "pval"]
    asterisks = get_asterisks(pval)
    if not asterisks and pval < .1:
        asterisks = "~"
    if asterisks:
        mean = within_df.loc[c, "mean"]
        which_ci = "hi" if mean > 0 else "lo"
        va = "bottom" if mean > 0 else "top"
        yloc = within_df.loc[c, f"ci_{which_ci}"]
        yloc = yloc + (.1 if mean > 0 else -.1)
        ax.text(x, yloc, asterisks, va=va, ha="center", fontsize=10)

# between conditions

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

for (c1, c2), row in between_df.iterrows():
    x1 = CONDITION_ORDER.index(c1)
    x2 = CONDITION_ORDER.index(c2)
    x1, x2 = sorted([x1, x2]) # to make sure x1 comes before x2
    asterisks = get_asterisks(row["pval"])
    if not asterisks and row["pval"] < .1:
        asterisks = "~"
    yloc = .77 if (x2-x1)>1 else .7
    draw_sig_bar(ax, x1, x2, yloc, asterisks)


#### Legend
handles = [ plt.matplotlib.patches.Patch(
        edgecolor="black", linewidth=.3,
        facecolor=palette[c], hatch=HATCH_STYLES[c],
        label=f"{c} cue"
    ) for c in CONDITION_ORDER ]
legend = ax.legend(handles=handles,
    # title="Cue following active cue",
    bbox_to_anchor=(0, 1), loc="upper left")
# legend._legend_box.align = "left"


#### Export
plt.savefig(export_fname)
utils.save_hires_copies(export_fname)
plt.close()