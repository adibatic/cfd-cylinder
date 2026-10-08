#!/usr/bin/env python3
"""Force coefficients and Strouhal number of one finished run.

Usage:
    python3 postprocessing/analyze_case.py --run medium --t-start 0.5

Reads runs/<run>/postProcessing, prints the results and the statistical
checks, writes figures to results/figures/ and one row of
results/tables/runs.csv.
"""
import argparse
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
D = 0.1       # m
U = 10.0      # m/s


# ---------------------------------------------------------------- reading

def read_coefficients(run_dir):
    """Time, C_D and C_L from postProcessing/forceCoeffs1/*/coefficient.dat.

    The columns are found by name in the '# Time ...' header line, so the
    order may change between OpenFOAM versions. A restarted run writes one
    folder per start time; the files are joined and repeated times dropped.
    """
    files = sorted(Path(run_dir).glob("postProcessing/forceCoeffs1/*/coefficient*.dat"),
                   key=lambda p: float(p.parent.name))
    if not files:
        raise FileNotFoundError(f"no coefficient file in {run_dir}/postProcessing/forceCoeffs1")
    t_all, cd_all, cl_all = [], [], []
    for path in files:
        names = None
        rows = []
        for line in path.read_text().splitlines():
            if line.startswith("#"):
                words = line[1:].split()
                if words and words[0] == "Time":
                    names = words
                continue
            if line.strip():
                rows.append([float(w) for w in line.split()])
        data = np.array(rows)
        t_all.append(data[:, names.index("Time")])
        cd_all.append(data[:, names.index("Cd")])
        cl_all.append(data[:, names.index("Cl")])
    t, cd, cl = (np.concatenate(a) for a in (t_all, cd_all, cl_all))
    t, keep = np.unique(t, return_index=True)    # sorted, repeated times dropped
    return t, cd[keep], cl[keep]


def cell_count(run_dir):
    """Number of cells, from the checkMesh log written by make_case.sh."""
    text = (Path(run_dir) / "log.checkMesh").read_text()
    return int(re.search(r"^\s*cells:\s+(\d+)", text, re.M).group(1))


# ---------------------------------------------------------------- signals

def uniform_times(t):
    """A uniform time axis fitted to the times written in the file.

    OpenFOAM writes times to 6 significant digits (timePrecision), so with
    dt = 2.5e-5 the time 1.000025 appears as 1.00003 and the spacing looks
    uneven. With a constant time step the written times lie on a straight
    line t0 + k dt to within that rounding; a least-squares line through all
    of them gives dt very precisely (t0 only to the rounding, which shifts
    every time equally and changes no statistic). A real change of time
    step, or a gap, leaves the line: that is an error.
    """
    k = np.arange(len(t))
    dt, t0 = np.polyfit(k, t, 1)
    uniform = t0 + dt * k
    if np.max(np.abs(t - uniform)) > 0.5 * dt:
        raise ValueError("time step is not constant; resample before the FFT")
    return uniform


def upward_crossings(t, x):
    """Times where x - mean(x) crosses zero going up, linearly interpolated."""
    y = x - x.mean()
    i = np.nonzero((y[:-1] < 0) & (y[1:] >= 0))[0]
    return t[i] - y[i] * (t[i + 1] - t[i]) / (y[i + 1] - y[i])


def whole_periods(t, cl):
    """Mask of the samples between the first and last upward crossing of C_L,
    and the number of whole periods in between."""
    c = upward_crossings(t, cl)
    if len(c) < 2:
        raise ValueError("fewer than two shedding cycles in the window")
    return (t >= c[0]) & (t <= c[-1]), len(c) - 1


def peak_frequency(t, x, pad=8):
    """Frequency of the largest peak of the spectrum of x (uniform t), in Hz.

    A Hann window keeps the mirror peak at -f from pulling the peak at +f.
    The zero-padded FFT finds the peak to within one bin; the frequency is
    then refined by maximizing |sum w(t) x(t) exp(-2 pi i f t)| between the
    neighbouring bins. Returns f and the FFT (frequencies, amplitudes).
    """
    from scipy.optimize import minimize_scalar

    dt = t[1] - t[0]
    y = (x - x.mean()) * np.hanning(len(x))
    n = pad * len(y)
    amp = np.abs(np.fft.rfft(y, n))
    freq = np.fft.rfftfreq(n, dt)
    k = int(np.argmax(amp[1:])) + 1

    def minus_amp(f):
        return -abs(np.sum(y * np.exp(-2j * np.pi * f * t)))

    res = minimize_scalar(minus_amp, bounds=(freq[k - 1], freq[k + 1]),
                          method="bounded", options={"xatol": 1e-9})
    return res.x, freq, amp


def statistics(t, cd, cl, t_start):
    """Mean C_D, rms C_L, Strouhal number and the convergence checks."""
    w = t >= t_start
    t, cd, cl = t[w], cd[w], cl[w]
    t = uniform_times(t)
    mask, n_periods = whole_periods(t, cl)
    t, cd, cl = t[mask], cd[mask], cl[mask]
    f, _, _ = peak_frequency(t, cl)
    crossings = upward_crossings(t, cl)
    f_cross = (len(crossings) - 1) / (crossings[-1] - crossings[0])
    # first and second half, each made of whole periods
    mid = crossings[len(crossings) // 2]
    cd1, cd2 = cd[t <= mid].mean(), cd[t >= mid].mean()
    return {
        "periods": n_periods,
        "f_Hz": f,
        "f_cross_Hz": f_cross,
        "St": f * D / U,
        "Cd_mean": cd.mean(),
        "Cd_amp": 0.5 * np.ptp(cd),
        "Cl_rms": np.sqrt(np.mean((cl - cl.mean()) ** 2)),
        "Cl_amp": 0.5 * np.ptp(cl),
        "Cd_half_diff_pct": 100 * abs(cd2 - cd1) / abs(cd.mean()),
    }


# ---------------------------------------------------------------- output

def figures(run, t, cd, cl, t_start, stats, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(2, 1, figsize=(7, 5), sharex=True)
    ax[0].plot(t, cd, lw=0.8)
    ax[0].axhline(stats["Cd_mean"], color="k", ls="--", lw=0.8)
    ax[0].set_ylabel("$C_D$")
    ax[1].plot(t, cl, lw=0.8)
    ax[1].set_ylabel("$C_L$")
    ax[1].set_xlabel("t (s)")
    # the impulsive start gives huge values in the first steps: scale the axes
    # to the flow after t_start / 5
    late = t > 0.2 * t_start
    for a, x in zip(ax, (cd, cl)):
        a.axvspan(t[0], t_start, color="0.9")
        lo, hi = x[late].min(), x[late].max()
        a.set_ylim(lo - 0.1 * (hi - lo), hi + 0.1 * (hi - lo))
    ax[0].set_title(f"{run}: grey = start-up, discarded")
    fig.tight_layout()
    fig.savefig(out / f"{run}_coefficients.png", dpi=150)
    plt.close(fig)

    w = t >= t_start
    mask, _ = whole_periods(t[w], cl[w])
    _, freq, amp = peak_frequency(t[w][mask], cl[w][mask])
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.plot(freq * D / U, amp / amp.max())
    ax.axvline(stats["St"], color="k", ls="--", lw=0.8)
    ax.set_xlim(0, 1)
    ax.set_xlabel("St = f D / U")
    ax.set_ylabel("|FFT($C_L$)|, normalized")
    ax.set_title(f"{run}: St = {stats['St']:.4f}")
    fig.tight_layout()
    fig.savefig(out / f"{run}_spectrum.png", dpi=150)
    plt.close(fig)


def save_row(table, run, stats):
    """Add or replace this run's row in the results table."""
    import pandas as pd

    row = pd.DataFrame([{"run": run, **stats}])
    if table.exists():
        old = pd.read_csv(table)
        row = pd.concat([old[old["run"] != run], row])
    row.sort_values("run").to_csv(table, index=False, float_format="%.6g")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True, help="folder name in runs/")
    ap.add_argument("--t-start", type=float, default=0.5, help="discard t < t-start (s)")
    args = ap.parse_args()
    run_dir = ROOT / "runs" / args.run
    figs = ROOT / "results" / "figures"
    tables = ROOT / "results" / "tables"
    figs.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)

    t, cd, cl = read_coefficients(run_dir)
    stats = statistics(t, cd, cl, args.t_start)
    stats["dt"] = t[1] - t[0]
    stats["cells"] = cell_count(run_dir)

    from pressure import base_pressure, plot_cp, pressure_coefficient
    theta, cp = pressure_coefficient(run_dir, U)
    stats["Cp_base"] = base_pressure(theta, cp)
    plot_cp(args.run, theta, cp, stats["Cp_base"], figs)

    print(f"run {args.run}: t = {t[0]:g} to {t[-1]:g} s, dt = {stats['dt']:g} s, "
          f"{stats['cells']} cells")
    for key in ("periods", "f_Hz", "f_cross_Hz", "St", "Cd_mean", "Cd_amp",
                "Cl_rms", "Cl_amp", "Cp_base", "Cd_half_diff_pct"):
        print(f"  {key:17s} {stats[key]:.5g}")
    ok_periods = stats["periods"] >= 15
    ok_halves = stats["Cd_half_diff_pct"] < 1.0
    print(f"  check: periods >= 15            {'PASS' if ok_periods else 'FAIL'}")
    print(f"  check: C_D halves differ < 1 %  {'PASS' if ok_halves else 'FAIL'}")

    figures(args.run, t, cd, cl, args.t_start, stats, figs)
    save_row(tables / "runs.csv", args.run, stats)
    print(f"  wrote results/figures/{args.run}_*.png and results/tables/runs.csv")


if __name__ == "__main__":
    main()