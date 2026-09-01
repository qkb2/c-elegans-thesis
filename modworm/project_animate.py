"""
modWorm: Modular simulation of neural connectomics, dynamics and biomechanics
of Caenorhabditis elegans

Standalone animation utilities.

Copyright (c) 2024-2025 University of Washington.
Developed in UW NeuroAI Lab by Jimin Kim.
"""

__author__ = "Jimin Kim: jk55@u.washington.edu"

import os
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from imageio.v2 import imread

from modWorm import sys_paths as paths
from modWorm import muscle_body_params as mb_params


# =============================================================================
# MASTER FUNCTIONS
# =============================================================================


def animate_body(
    x,
    y,
    filename,
    xmin,
    xmax,
    ymin,
    ymax,
    figsize_x,
    figsize_y,
    background_img_path=None,
    animation_config=None,
    output_dir=None,
):
    """
    Create an MP4 animation of the worm body.

    Parameters
    ----------
    x, y : np.ndarray
        Arrays of shape (n_frames, n_segments) containing the x/y coordinates
        of each worm segment.

    filename : str
        Output filename, with or without the .mp4 extension.

    xmin, xmax, ymin, ymax : float
        Axis limits.

    figsize_x, figsize_y : float
        Figure dimensions in inches.

    background_img_path : str or Path, optional
        Path to a background image.

    animation_config : object, optional
        Animation configuration. Defaults to mb_params.CE_animation.

    output_dir : str or Path, optional
        Directory in which to save the animation.
        Defaults to paths.videos_dir.

    Returns
    -------
    pathlib.Path
        Path to the generated MP4 file.
    """

    if animation_config is None:
        animation_config = mb_params.CE_animation

    # -------------------------------------------------------------------------
    # Validate input
    # -------------------------------------------------------------------------

    x = np.asarray(x)
    y = np.asarray(y)

    if x.ndim != 2 or y.ndim != 2:
        raise ValueError("x and y must be 2-dimensional arrays.")

    if x.shape != y.shape:
        raise ValueError(
            f"x and y must have the same shape. Got x={x.shape}, y={y.shape}."
        )

    if x.shape[0] == 0:
        raise ValueError("x and y must contain at least one frame.")

    # -------------------------------------------------------------------------
    # Background image
    # -------------------------------------------------------------------------

    img = None

    if background_img_path is not None:
        background_img_path = Path(background_img_path)

        if not background_img_path.exists():
            raise FileNotFoundError(
                f"Background image not found: {background_img_path}"
            )

        img = imread(background_img_path)

    # -------------------------------------------------------------------------
    # Output path
    # -------------------------------------------------------------------------

    if output_dir is None:
        output_dir = Path(paths.videos_dir)
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    filename = Path(filename)

    if filename.suffix.lower() != ".mp4":
        filename = filename.with_suffix(".mp4")

    output_path = output_dir / filename

    # -------------------------------------------------------------------------
    # Figure
    # -------------------------------------------------------------------------

    segment_count = x.shape[1]

    fig, ax = initialize_figure(
        figsize_x,
        figsize_y,
        xmin,
        xmax,
        ymin,
        ymax,
    )

    # -------------------------------------------------------------------------
    # Background
    # -------------------------------------------------------------------------

    if img is not None:
        ax.imshow(
            img,
            zorder=0,
            extent=[xmin, xmax, ymin, ymax],
        )

    # -------------------------------------------------------------------------
    # Worm body
    # -------------------------------------------------------------------------

    patch_list = render_body(
        x,
        y,
        animation_config,
        segment_count,
    )

    for patch in patch_list:
        ax.add_patch(patch)

    # -------------------------------------------------------------------------
    # Animation callbacks
    # -------------------------------------------------------------------------

    def init():
        for k, patch in enumerate(patch_list[:segment_count]):
            patch.center = (x[0, k], y[0, k])

        return patch_list

    def animate(frame):
        # Update worm segments.
        for k in range(segment_count):
            patch = patch_list[k]
            patch.center = (x[frame, k], y[frame, k])

        # Add trail point if requested.
        if getattr(animation_config, "display_trail", False):
            trail_point = animation_config.trail_point

            trail = plt.Circle(
                (
                    x[frame, trail_point],
                    y[frame, trail_point],
                ),
                animation_config.trail_width,
                color=animation_config.trail_color,
                alpha=0.7,
            )

            patch_list.append(trail)
            ax.add_patch(trail)

        return patch_list

    # -------------------------------------------------------------------------
    # Writer
    # -------------------------------------------------------------------------

    try:
        Writer = animation.writers["ffmpeg"]
    except RuntimeError as exc:
        raise RuntimeError(
            "FFmpeg is required to create MP4 animations. "
            "Install FFmpeg and make sure it is available on PATH."
        ) from exc

    writer = Writer(
        fps=animation_config.fps,
        metadata={"artist": "Jimin Kim"},
        bitrate=1800,
    )

    # -------------------------------------------------------------------------
    # Create animation
    # -------------------------------------------------------------------------

    anim = animation.FuncAnimation(
        fig,
        func=animate,
        init_func=init,
        frames=x.shape[0],
        interval=animation_config.interval,
        blit=True,
    )

    ax.axis(animation_config.display_axis)

    # -------------------------------------------------------------------------
    # Save
    # -------------------------------------------------------------------------

    try:
        anim.save(
            str(output_path),
            writer=writer,
            savefig_kwargs={"facecolor": animation_config.facecolor},
        )
    finally:
        plt.close(fig)

    print(f"Animation saved to: {output_path}")

    return output_path


# =============================================================================
# PREPARATION FUNCTIONS
# =============================================================================


def initialize_figure(
    figsize_x,
    figsize_y,
    xmin,
    xmax,
    ymin,
    ymax,
):
    """
    Initialize the Matplotlib figure and axes.
    """

    fig = plt.figure(
        figsize=(figsize_x, figsize_y),
        dpi=100,
    )

    ax = fig.add_axes(
        [0.0, 0.0, 1.0, 1.0],
        xlim=(xmin, xmax),
        ylim=(ymin, ymax),
    )

    return fig, ax


def render_body(
    x,
    y,
    animation_config,
    segment_count,
):
    """
    Create Matplotlib Circle objects representing worm segments.
    """

    patch_list = []

    diameters = animation_config.diameter_scaler * mb_params.CE_animation.h_interp(
        np.linspace(
            0,
            mb_params.CE.h_num,
            segment_count,
        )
    )

    radius = np.divide(diameters, 1.5)

    worm_color = animation_config.worm_seg_color

    for k in range(segment_count):
        if isinstance(worm_color, str):
            color = worm_color
        else:
            color = worm_color[k]

        patch = plt.Circle(
            (x[0, k], y[0, k]),
            radius[k],
            color=color,
        )

        patch_list.append(patch)

    return patch_list
