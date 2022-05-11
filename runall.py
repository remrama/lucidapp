import subprocess

file_basenames = [
    "setup-directories",
    "setup-source2csv",
    "setup-merge+clean",
    "describe-samplesize",
    "describe-demographics",
    "describe-correlations",
    "analyze-app_effect",
    "analyze-cue_effect",
    # "plot-app_effect", <--- doesn't exist yet
    "plot-cue_effect",
]

for bn in file_basenames:
    cmd = f"python ./{bn}.py"
    print(cmd)
    p = subprocess.run(cmd, check=False)
    if p.returncode != 0:
        break