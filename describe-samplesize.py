"""Massive calendar view of sample.
This big mess is designed to get a sense of:
    - how many participants there were
    - how long participants participated for (ie, how many sessions per participant)
    - how many trials there were during each session
    - how long the gaps between sessions were
"""
import os
import numpy as np
import utils

import seaborn as sea # for color palette
import matplotlib.pyplot as plt
utils.load_matplotlib_settings()


#### Choose export path.
data_dir = utils.Config.data_directory
export_fname = os.path.join(data_dir, "results", "describe-samplesize.png")


#### Load data.
df = utils.load_data("trials")


#### Wrangle/reshape data.

# Convert timestamps to dates (ie, day only).
df["date"] = df["timeStart"].dt.date

# Pivot a table with columns for each date and cells that
# count how many dream reports there were for that session/date.
table = df.groupby(["subjectID", "sessionID"]
    )["date"].agg(["count", "first"]
    ).reset_index(
    ).pivot_table(index="subjectID", columns="first", values="count")

# Sort the table by participant based on earliest start date and number of total sessions.
n_sessions = table.notna().sum(axis=1).rename("n_sessions")
first_session = table.apply(lambda s: s.dropna().index[0], axis=1)
sorter_df = first_session.to_frame("first_session"
    ).join(n_sessions.to_frame("n_sessions")
    ).sort_values(["first_session", "n_sessions"], ascending=[True, False])
table = table.reindex(index=sorter_df.index)


#### Draw plot.

# define parameters
FIGSIZE = (5, 4)
PCOLORMESH_KWARGS = dict(shading="nearest", linewidth=0, edgecolors="black")
cmap = sea.dark_palette("#69d", reverse=True, as_cmap=True)

# open figure and axis
fig, ax = plt.subplots(figsize=FIGSIZE)

# draw the many little squares
ax.grid(False)
im = ax.pcolormesh(table.columns, range(table.index.size), table,
    cmap=cmap, **PCOLORMESH_KWARGS)

# adjust aesthetics
ax.xaxis.tick_top()
ax.xaxis.set_label_position("top") 
ax.tick_params(which="both", labelleft=False, left=False, top=False, right=False)
ax.set_ylabel("Participant", labelpad=5)
ax.set_xlabel(r"$\rightarrow$   Date of session   $\rightarrow$", labelpad=5)
locator = plt.matplotlib.dates.AutoDateLocator()
formatter = plt.matplotlib.dates.ConciseDateFormatter(locator)
ax.xaxis.set(major_locator=locator, major_formatter=formatter)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["top"].set_position(("outward", 5))
ax.spines["left"].set_position(("outward", 5))
ax.invert_yaxis()

# draw colorbar
cbar_max = np.nanmax(table.values)
cbar_ticks = [1, cbar_max]
cax = ax.inset_axes([.02, .05, .15, .03])
cax.grid(False)
cbar = fig.colorbar(im, cax=cax, orientation="horizontal", ticklocation="bottom")
cbar.set_ticks(cbar_ticks)
cbar.ax.tick_params(which="both", direction="out", top=False)
cbar.ax.xaxis.set(minor_locator=plt.MultipleLocator(1))
cbar.ax.set_title(r"$n$ trials per session", pad=5)


# open new axis for histogram insert
axin = ax.inset_axes([.65, .8, .3, .15])

# define histogram bins
sessions = n_sessions.sort_values().unique()
bins = np.arange(sessions.min()-.5, sessions.size+1)

# draw histogram
axin.hist(n_sessions, bins=bins, density=False,
    color="white", edgecolor="black", linewidth=1)

# adjust aesthetics on histogram
axin.set_xlim(bins[0]-.5, bins[-1]+.5)
axin.set_ybound(upper=240)
axin.set_xlabel(r"$n$ sessions")
axin.set_ylabel(r"$n$ participants")
axin.xaxis.set(major_locator=plt.MultipleLocator(1))
axin.tick_params(top=False)
axin.yaxis.set(major_locator=plt.MultipleLocator(100),
               minor_locator=plt.MultipleLocator(20))


#### Export.
plt.savefig(export_fname)
utils.save_hires_copies(export_fname)
plt.close()