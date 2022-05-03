"""Demographic visualizations. (just age)
"""
import os
import pandas as pd
import utils
import matplotlib.pyplot as plt
utils.load_matplotlib_settings()


#### Choose import/export paths.
data_dir = utils.Config.data_directory
import_fname = os.path.join(data_dir, "derivatives", "participants-clean.csv")
export_fname = os.path.join(data_dir, "results", "describe-demographics.png")


#### Load data.
df = pd.read_csv(import_fname)


#### Define parameters.
FIGSIZE = (2, 2.2)
HIST_KWARGS = dict(bins=20, linewidth=.5, edgecolor="black")
CONDITION_ORDER = ["control", "sham", "active"]
palette = utils.load_config(as_object=False)["colors"]


#### Draw plot.

# open the figure
fig, (ax1, ax2) = plt.subplots(nrows=2, figsize=FIGSIZE,
    sharex=True, sharey=True, gridspec_kw=dict(hspace=.1))

# draw the bottom histogram (all data colored equally)
ax2.hist("age", data=df, color="gainsboro", **HIST_KWARGS)

# draw the top histogram (separate colors for different conditions)
colors = [ palette[c] for c in CONDITION_ORDER ]
data = df.groupby("subjectCondition")["age"].apply(list).loc[CONDITION_ORDER]
ax1.hist(data, color=colors, histtype="barstacked", **HIST_KWARGS)

# draw the legend
handles = [ plt.matplotlib.patches.Patch(edgecolor="none",
    facecolor=palette[c], label=c) for c in CONDITION_ORDER ]
legend = ax1.legend(handles=handles,
    title="Group Cue Condition",
    bbox_to_anchor=(1, 1), loc="upper right")

# aesthetic adjustments
ax2.set_xlabel("Reported age (years)")
ax2.set_ylabel(r"$n$ participants")
ax1.tick_params(axis="x", which="both", top=False, bottom=False)
ax2.tick_params(axis="x", which="both", direction="out", top=False)


#### Export!
plt.savefig(export_fname)
utils.save_hires_copies(export_fname)
plt.close()