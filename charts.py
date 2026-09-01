import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# original data
data_general = [
    {"Project": "OpenWorm", "Neurons": 302, "Body_Sim": True, "Training_Method": "genetic algorithm (bionet)", "Training_Space_MB": None, "Sim_Space_MB": 410},
    {"Project": "BAAIWorm", "Neurons": 136, "Body_Sim": True, "Training_Method": "gradient descent-based (eworm-learn: BPTT-based)", "Training_Space_MB": None, "Sim_Space_MB": None},
    {"Project": "Digital Twin", "Neurons": 329, "Body_Sim": True, "Training_Method": "gradient descent-based (BPTT)", "Training_Space_MB": None, "Sim_Space_MB": None},
    {"Project": "WormSim", "Neurons": 302, "Body_Sim": True, "Training_Method": "n.a.", "Training_Space_MB": None, "Sim_Space_MB": 17},
    {"Project": "ModWorm", "Neurons": 279, "Body_Sim": True, "Training_Method": "n.a.", "Training_Space_MB": None, "Sim_Space_MB": 1320},
    {"Project": "Sakamoto (2021)", "Neurons": 79, "Body_Sim": False, "Training_Method": "gradient descent-based (BPTT)", "Training_Space_MB": 1564, "Sim_Space_MB": None},
    {"Project": "Zhuo (2024)", "Neurons": 14, "Body_Sim": False, "Training_Method": "Gradient descent", "Training_Space_MB": 1550, "Sim_Space_MB": None}, # 1346 + 204
    {"Project": "Barbulescu (2023)", "Neurons": 8, "Body_Sim": False, "Training_Method": "Gradient descent", "Training_Space_MB": 575, "Sim_Space_MB": None},
    {"Project": "Liu (2018)", "Neurons": 279, "Body_Sim": False, "Training_Method": "no typical learning, SVD used in the pipeline", "Training_Space_MB": 225, "Sim_Space_MB": 225},
    {"Project": "Kim (2019)", "Neurons": 279, "Body_Sim": False, "Training_Method": "n.a.", "Training_Space_MB": None, "Sim_Space_MB": 103},
]
df = pd.DataFrame(data_general)

sns.set_theme(style="whitegrid")

# 1. RAM usage in training
df_train = df.dropna(subset=["Training_Space_MB"]).sort_values("Training_Space_MB", ascending=False)
fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(df_train["Project"], df_train["Training_Space_MB"], color="#3b5998", edgecolor="none", width=0.55)
ax.set_title("RAM Usage in Training", fontsize=14, fontweight="bold", pad=15)
ax.set_ylabel("Memory (MB)", fontsize=11)
ax.tick_params(axis="x", rotation=25, labelsize=10)
ax.bar_label(bars, padding=4, fmt="%.0f MB", fontsize=10, fontweight="bold")
plt.tight_layout()
plt.savefig("ram_usage_training.png", dpi=300)
plt.close()

# 2. RAM usage in simulation
df_sim = df.dropna(subset=["Sim_Space_MB"]).sort_values("Sim_Space_MB", ascending=False)
fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(df_sim["Project"], df_sim["Sim_Space_MB"], color="#2e8b57", edgecolor="none", width=0.55)
ax.set_title("RAM Usage in Simulation", fontsize=14, fontweight="bold", pad=15)
ax.set_ylabel("Memory (MB)", fontsize=11)
ax.tick_params(axis="x", rotation=25, labelsize=10)
ax.bar_label(bars, padding=4, fmt="%.0f MB", fontsize=10, fontweight="bold")
plt.tight_layout()
plt.savefig("ram_usage_simulation.png", dpi=300)
plt.close()

# 3. Number of neurons implemented
df_neurons = df.sort_values("Neurons", ascending=False)
fig, ax = plt.subplots(figsize=(10, 5.5))
bars = ax.bar(df_neurons["Project"], df_neurons["Neurons"], color="#c0392b", edgecolor="none", width=0.6)
ax.set_title("Number of Neurons Implemented", fontsize=14, fontweight="bold", pad=15)
ax.set_ylabel("Neuron Count", fontsize=11)
ax.tick_params(axis="x", rotation=35, labelsize=10)
ax.bar_label(bars, padding=4, fmt="%d", fontsize=10, fontweight="bold")
plt.tight_layout()
plt.savefig("neurons_implemented.png", dpi=300)
plt.close()