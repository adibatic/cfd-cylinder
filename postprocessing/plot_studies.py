#!/usr/bin/env python3
"""Comparison figures of the mesh study, the time-step study and the validation.

Usage:
    python3 postprocessing/plot_studies.py

Reads results/tables/ (runs.csv, gci_mesh.csv, gci_time.csv, validation.csv)
and the runs in runs/, writes PNG files to results/figures/. A figure whose
input is missing is skipped with a message.
"""
from pathlib import Path

import numpy as np

from analyze_case import ROOT, U, read_coefficients
from pressure import pressure_coefficient

TABLES = ROOT / "results" / "tables"
FIGS = ROOT / "results" / "figures"
MESHES = ["coarse", "medium", "fine"]
STEPS = ["medium-dt1e-4", "medium", "medium-dt2.5e-5"]
# fixed colour per run, the same in every figure
COLOR = {"coarse": "#2a78d6", "medium": "#eb6834", "fine": "#1baf7a",
         "medium-dt1e-4": "#eda100", "medium-dt2.5e-5": "#e87ba4"}
LABEL = {"Cd_mean": "mean $C_D$", "St": "St", "Cl_rms": "rms $C_L$", "Cp_base": "base $C_p$"}


def plt_():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"axes.grid": True, "grid.alpha": 0.3, "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    return plt


def save(fig, name):
    FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGS / name, dpi=150, bbox_inches="tight")
    print("wrote results/figures/" + name)


def finished(run):
    """True when runs/<run> exists and its solver log ends with End."""
    log = ROOT / "runs" / run / "log.pimpleFoam"
    return log.exists() and "\nEnd\n" in log.read_text()[-2000:]


def convergence(plt, runs, kind, gci_file, name):
    """Each quantity against h / h_1 (or dt / dt_1), with phi_ext and the GCI band."""
    import pandas as pd

    table = pd.read_csv(TABLES / "runs.csv").set_index("run")
    if not all(r in table.index for r in runs) or not (TABLES / gci_file).exists():
        print(f"skip {name}: runs or {gci_file} missing")
        return
    g = pd.read_csv(TABLES / gci_file).set_index("quantity")
    rows = table.loc[runs[::-1]]                  # finest first
    h = (1 / np.sqrt(rows["cells"].to_numpy())) if kind == "mesh" else rows["dt"].to_numpy()
    h = h / h[0]
    # 2 x 2, close to the 4:3 of the other figures, so it stays readable in the README gallery
    fig, axes = plt.subplots(2, 2, figsize=(9, 6))
    fig.subplots_adjust(wspace=0.4, hspace=0.55, top=0.86)  # room for the labels and titles
    axes = axes.ravel()
    for ax, q in zip(axes, LABEL):
        phi = rows[q].to_numpy()
        ax.plot(h, phi, "-", color="0.6", lw=1, zorder=1)
        for x, y, r in zip(h, phi, rows.index):
            ax.plot(x, y, "o", ms=8, color=COLOR[r], mec="white", mew=2, zorder=3, label=r)
        ext, band = g.loc[q, "phi_ext"], g.loc[q, "u_num"] * abs(phi[0])
        if np.isfinite(ext) and not g.loc[q, "oscillatory"]:
            ax.plot(0, ext, "s", ms=7, color="0.2", zorder=3, label="extrapolated")
        if np.isfinite(band):
            ax.errorbar(h[0], phi[0], yerr=band, color="0.2", capsize=4, lw=1, zorder=2)
        ax.set_xlim(-0.1, h[-1] * 1.1)
        ax.set_title(LABEL[q])
        ax.set_xlabel("h / h_fine" if kind == "mesh" else "Δt / Δt_smallest")
    axes[0].legend(fontsize=8, frameon=False)
    fig.suptitle(("Mesh study" if kind == "mesh" else "Time-step study (medium mesh)")
                 + "\nbar = u_num on the finest, square = extrapolated value (monotonic only)",
                 fontsize=10)
    save(fig, name)
    plt.close(fig)


def lift_overlay(plt):
    if not all(finished(r) for r in MESHES):
        print("skip cl_three_meshes.png: coarse, medium and fine must have finished")
        return
    fig, ax = plt.subplots(figsize=(8, 3.2))
    for r in MESHES:
        t, _, cl = read_coefficients(ROOT / "runs" / r)
        w = t >= 1.3
        ax.plot(t[w], cl[w], lw=2, color=COLOR[r], label=r)
    ax.set_xlabel("t (s)")
    ax.set_ylabel("$C_L$")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1))
    ax.set_title("Lift on three meshes, last 0.2 s")
    save(fig, "cl_three_meshes.png")
    plt.close(fig)


def cp_overlay(plt):
    if not all(finished(r) for r in MESHES):
        print("skip cp_three_meshes.png: coarse, medium and fine must have finished")
        return
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for r in MESHES:
        theta, cp = pressure_coefficient(ROOT / "runs" / r, U)
        ax.plot(theta, cp, lw=2, color=COLOR[r], label=r)
    th = np.linspace(0, 180, 181)
    ax.plot(th, 1 - 4 * np.sin(np.radians(th)) ** 2, ":", color="0.4", lw=1.5,
            label="potential flow")
    ax.set_xlim(0, 180)
    ax.set_xlabel(r"$\theta$ (deg from the front stagnation point)")
    ax.set_ylabel("time-averaged $C_p$")
    ax.legend(frameon=False)
    ax.set_title("Pressure on the cylinder, three meshes")
    save(fig, "cp_three_meshes.png")
    plt.close(fig)


def validation(plt):
    import pandas as pd

    path = TABLES / "validation.csv"
    if not path.exists():
        print("skip validation.png: results/tables/validation.csv missing (run validation/compare.py)")
        return
    v = pd.read_csv(path)
    fig, axes = plt.subplots(1, len(v), figsize=(3.2 * len(v), 3.2), squeeze=False)
    for ax, (_, r) in zip(axes[0], v.iterrows()):
        ax.errorbar([0], [r["S"]], yerr=[r["U_num"]], fmt="o", ms=8, color=COLOR["fine"],
                    capsize=5, label="simulation ± U_num")
        ax.errorbar([1], [r["D"]], yerr=[r["U_D"]], fmt="s", ms=8, color="0.3",
                    capsize=5, label="experiment ± U_D")
        ax.set_xticks([0, 1], ["CFD", "exp."])
        ax.set_xlim(-0.6, 1.6)
        ax.set_title(LABEL.get(r["quantity"], r["quantity"]))
    axes[0][0].legend(fontsize=8, frameon=False)
    fig.suptitle("Validation: fine mesh vs experiments", y=1.04)
    save(fig, "validation.png")
    plt.close(fig)


def main():
    plt = plt_()
    convergence(plt, MESHES, "mesh", "gci_mesh.csv", "mesh_convergence.png")
    convergence(plt, STEPS, "time", "gci_time.csv", "time_step_convergence.png")
    lift_overlay(plt)
    cp_overlay(plt)
    validation(plt)


if __name__ == "__main__":
    main()
