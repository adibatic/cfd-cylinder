#!/usr/bin/env python3
"""Vorticity snapshot, video, and looping GIF of one run.

Usage:
    python3 postprocessing/animate_vorticity.py --run medium-anim

Needs the vorticity field in every time folder and the cell centres C in
one of them: run 'postProcess -func vorticity' in the run folder (C is
written by scripts/run_case.sh). Writes the last frame to
results/figures/vorticity_<run>.png and, with ffmpeg, the video
media/vorticity_<run>.mp4 (media/ is not committed) and the looping GIF
results/animations/vorticity_<run>.gif for the README.
"""
import argparse
import csv
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
R = 0.05                             # cylinder radius (m)
WINDOW = (-0.3, 1.5, -0.45, 0.45)    # video: x_min, x_max, y_min, y_max (m)
GIF_WINDOW = (-0.2, 1.5, -0.3, 0.3)  # GIF: a wide strip around the wake (m)


def read_internal_vectors(field_file):
    """internalField of an ASCII volVectorField as an (n, 3) array."""
    text = Path(field_file).read_text()
    m = re.search(r"internalField\s+nonuniform\s+List<vector>\s*(\d+)\s*\(", text)
    n = int(m.group(1))
    body = text[m.end(): text.index("boundaryField")]
    values = np.array([float(w) for w in re.findall(r"[-+0-9.eE]+", body)])
    return values[: 3 * n].reshape(n, 3)


def time_dirs(run_dir):
    return sorted((p for p in Path(run_dir).iterdir()
                   if p.is_dir() and re.fullmatch(r"[0-9.eE+-]+", p.name)
                   and (p / "vorticity").exists()),
                  key=lambda p: float(p.name))


def triangulation(xy):
    """Delaunay triangles of the cell centres in the window, without the cylinder."""
    import matplotlib.tri as mtri

    tri = mtri.Triangulation(xy[:, 0], xy[:, 1])
    cx = xy[tri.triangles, 0].mean(axis=1)
    cy = xy[tri.triangles, 1].mean(axis=1)
    tri.set_mask(np.hypot(cx, cy) < R)
    return tri


def shedding_frequency(run):
    """f_Hz of the run this one continues ('medium-anim' -> 'medium'), from runs.csv."""
    table = ROOT / "results" / "tables" / "runs.csv"
    source = run.removesuffix("-anim")
    if table.exists():
        for row in csv.DictReader(table.open()):
            if row["run"] == source:
                return float(row["f_Hz"])
    raise SystemExit(f"no f_Hz for {source} in {table}; pass --frequency")


def loop_frames(dt_frame, f, n_available):
    """Frames covering the whole number of periods that loops most smoothly.

    A loop of n frames joins seamlessly if n * dt_frame is a whole number k of
    shedding periods. Returns (n, k, error), the error in periods.
    """
    best = None
    for k in range(1, int((n_available - 1) * dt_frame * f) + 1):
        n = round(k / (f * dt_frame))
        error = abs(n * dt_frame * f - k)
        if best is None or error < best[2] - 1e-12:
            best = (n, k, error)
    if best is None:
        raise SystemExit("the run is shorter than one shedding period")
    return best


def draw(ax, tri, wz, levels, window):
    """Filled vorticity contours and the cylinder, clipped to the window."""
    from matplotlib.patches import Circle

    ax.tricontourf(tri, wz, levels=levels, cmap="RdBu_r", extend="both")
    ax.add_patch(Circle((0, 0), R, color="0.3"))
    ax.set_xlim(window[0], window[1])
    ax.set_ylim(window[2], window[3])
    ax.set_aspect("equal")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True)
    ap.add_argument("--limit", type=float, default=400.0, help="colour range +-limit (1/s)")
    ap.add_argument("--frequency", type=float, help="shedding frequency (Hz); default from runs.csv")
    args = ap.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    run_dir = ROOT / "runs" / args.run
    times = time_dirs(run_dir)
    if not times:
        raise SystemExit(f"no vorticity in {run_dir}; run the postProcess commands first")
    centres = next(t / "C" for t in reversed(times) if (t / "C").exists())
    xyz = read_internal_vectors(centres)
    x0, x1, y0, y1 = WINDOW
    keep = (xyz[:, 0] > x0 - 0.05) & (xyz[:, 0] < x1 + 0.05) & \
           (xyz[:, 1] > y0 - 0.05) & (xyz[:, 1] < y1 + 0.05)
    tri = triangulation(xyz[keep, :2])
    levels = np.linspace(-args.limit, args.limit, 41)

    frames = ROOT / "media" / f"frames_{args.run}"
    clean = ROOT / "media" / f"gif_frames_{args.run}"
    for d in (frames, clean):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
    for k, t in enumerate(times):
        wz = np.clip(read_internal_vectors(t / "vorticity")[keep, 2], -args.limit, args.limit)

        # video frame: axes, units, and the time
        fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=150)
        draw(ax, tri, wz, levels, WINDOW)
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        ax.set_title(f"vorticity $\\omega_z$, Re = 66,667, t = {float(t.name):.4f} s"
                     f"   (red: counter-clockwise, blue: clockwise)")
        fig.tight_layout()
        fig.savefig(frames / f"frame_{k:04d}.png")
        plt.close(fig)

        # GIF frame: no axes and no clock, so the loop has no visible jump
        gx0, gx1, gy0, gy1 = GIF_WINDOW
        fig = plt.figure(figsize=(9.6, 9.6 * (gy1 - gy0) / (gx1 - gx0)), dpi=100)
        ax = fig.add_axes((0, 0, 1, 1))
        draw(ax, tri, wz, levels, GIF_WINDOW)
        ax.set_axis_off()
        fig.savefig(clean / f"frame_{k:04d}.png")
        plt.close(fig)

    figs = ROOT / "results" / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    shutil.copy(frames / f"frame_{len(times) - 1:04d}.png", figs / f"vorticity_{args.run}.png")
    print(f"{len(times)} frames, t = {times[0].name} to {times[-1].name} s")
    print(f"wrote results/figures/vorticity_{args.run}.png")

    if not shutil.which("ffmpeg"):
        print("ffmpeg not found: frames are in", frames.relative_to(ROOT))
        return
    video = ROOT / "media" / f"vorticity_{args.run}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "20",
                    "-i", str(frames / "frame_%04d.png"),
                    "-vf", "scale=1920:-2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    str(video)], check=True)
    print(f"wrote media/{video.name}")

    f = args.frequency or shedding_frequency(args.run)
    dt_frame = (float(times[-1].name) - float(times[0].name)) / (len(times) - 1)
    n, periods, error = loop_frames(dt_frame, f, len(times))
    anims = ROOT / "results" / "animations"
    anims.mkdir(parents=True, exist_ok=True)
    gif = anims / f"vorticity_{args.run}.gif"
    palette = ("scale=800:-1:flags=lanczos,split[a][b];"
               "[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=sierra2_4a")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "25",
                    "-i", str(clean / "frame_%04d.png"), "-frames:v", str(n),
                    "-vf", palette, "-loop", "0", str(gif)], check=True)
    print(f"wrote results/animations/{gif.name}: {n} frames = {periods} periods "
          f"(seam {error:.2f} periods), {gif.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
