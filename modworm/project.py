import os
from pathlib import Path

import numpy as np

from modWorm import (
    # animation,
    predefined_classes_mb,
    predefined_classes_nv,
    sys_paths,
    utils,
)
from modWorm import body_dynamics as b_dyn
from modWorm import body_simulations as b_sim
from modWorm import muscle_body_params as mb_params
from modWorm import muscle_dynamics as m_dyn
from modWorm import network_dynamics as n_dyn
from modWorm import network_interactions as n_inter
from modWorm import network_params as n_params
from modWorm import network_simulations as n_sim
from modWorm import proprioception_simulation as p_sim

import project_animate as animation

# matplotlib must be imported after modWorm (PyCall fails otherwise)
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent

# Construct gap, synaptic connectomes and muscle map from downloaded files
conn_gap, conn_syn = utils.construct_connectome_Varshney(BASE_DIR / "NeuronConnect.xls")
muscle_map = utils.construct_muscle_map_Hall(BASE_DIR / "./NeuronFixedPoints.xls")

print("Maps constructed")


celegans_nv = predefined_classes_nv.CelegansWorm_NervousSystem_PPC_Julia(
    conn_gap, conn_syn
)
celegans_mb = predefined_classes_mb.CelegansWorm_MuscleBody_PPC_Julia(muscle_map)

# We use the pulse of neural stimuli emulating the gentle touch to C.elegans posterior body region
# input_mat has dim = (1400, 279) (14 seconds)

gentle_posterior_stim = np.load("modWorm/presets_input/input_mat_gentle_post_touch.npy")

print("Loaded nv, mb, stim")

# Pre-defined stimuli array inject decaying stimuli into PLM neurons

plt.plot(np.arange(0, 14, 0.01)[:400], gentle_posterior_stim[:400, 276])
plt.xlabel("Seconds")
plt.ylabel("pA")

# Use run_network() function from "proprioception_simulation" module NOT "network_simulation" module

solution_dict_fwd = p_sim.run_network_julia(
    celegans_nv, celegans_mb, gentle_posterior_stim
)

solution_dict_fwd.keys()

print("Got solutions.")

# Plot the body trajectory

plt.plot(solution_dict_fwd["x_solution"][:, 0], solution_dict_fwd["y_solution"][:, 0])
plt.xlim(-75, 75)
plt.ylim(-75, 75)

animation.animate_body(
    x=solution_dict_fwd["x_solution"],
    y=solution_dict_fwd["y_solution"],
    filename="fwd_locomotion_ppc",
    xmin=-70,
    xmax=20,
    ymin=-20,
    ymax=70,
    figsize_x=10,
    figsize_y=10,
    animation_config=mb_params.CE_animation,
)
