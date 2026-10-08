"""Time-averaged pressure coefficient on the cylinder.

Reads the ASCII fields pMean (written by the fieldAverage function object)
and C (face centres, written by 'postProcess -func writeCellCentres') from
the last time directory of a run.
"""
import re
from pathlib import Path

import numpy as np


def read_patch_values(field_file, patch):
    """Values of one patch in an ASCII OpenFOAM field file, as an array.

    Scalars give shape (n,), vectors (n, 3). Handles 'uniform' and
    'nonuniform List<...> n ( ... )'.
    """
    text = Path(field_file).read_text()
    text = text[text.index("boundaryField"):]
    m = re.search(r"^\s*" + re.escape(patch) + r"\s*\{", text, re.M)
    if m is None:
        raise KeyError(f"patch {patch} not in {field_file}")
    block = text[m.end():]
    v = re.search(r"\bvalue\s+(uniform|nonuniform)", block)
    if v is None:
        raise KeyError(f"patch {patch} in {field_file} has no value")
    rest = block[v.end():]
    if v.group(1) == "uniform":
        token = rest.split(";", 1)[0].strip()
        return np.array([float(w) for w in token.strip("()").split()])
    head = re.match(r"\s*List<(\w+)>\s*(\d+)\s*\(", rest)
    kind, n = head.group(1), int(head.group(2))
    body = rest[head.end():]
    values = np.array([float(w) for w in re.findall(r"[-+0-9.eE]+", body[: body.index(";")])])
    if kind == "vector":
        return values[: 3 * n].reshape(n, 3)
    return values[:n]


def last_time_dir(run_dir):
    """The time directory with the largest time."""
    times = [p for p in Path(run_dir).iterdir()
             if p.is_dir() and re.fullmatch(r"[0-9.eE+-]+", p.name) and float(p.name) > 0]
    return max(times, key=lambda p: float(p.name))


def pressure_coefficient(run_dir, u_inf):
    """theta (deg from the front stagnation point) and C_p on the cylinder.

    C_p = (pMean - p_inf) / (0.5 U^2) with the kinematic pressure p/rho and
    p_inf = mean pMean on the inlet patch. The upper and lower halves are
    folded onto 0..180 deg.
    """
    last = last_time_dir(run_dir)
    p = read_patch_values(last / "pMean", "cylinder")
    xyz = read_patch_values(last / "C", "cylinder")
    p_inf = read_patch_values(last / "pMean", "inlet").mean()
    theta = np.degrees(np.arctan2(np.abs(xyz[:, 1]), -xyz[:, 0]))
    cp = (p - p_inf) / (0.5 * u_inf**2)
    order = np.argsort(theta)
    return theta[order], cp[order]


def base_pressure(theta, cp):
    """C_p at the rear point (theta = 180 deg): mean of the two nearest faces."""
    return cp[np.argsort(theta)[-2:]].mean()


def plot_cp(run, theta, cp, cp_base, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(theta, cp, ".", ms=3)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel(r"$\theta$ (deg from the front stagnation point)")
    ax.set_ylabel("time-averaged $C_p$")
    ax.set_xlim(0, 180)
    ax.set_title(f"{run}: base $C_p$ = {cp_base:.3f}")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / f"{run}_cp.png", dpi=150)
    plt.close(fig)