#!/usr/bin/env python3
"""Grid convergence index of three runs (Celik et al. 2008).

Usage:
    python3 verification/gci.py mesh  fine medium coarse
    python3 verification/gci.py time  medium-dt2.5e-5 medium medium-dt1e-4

The runs are listed finest first. 'mesh' measures the refinement by the
cell count (2-D: h = (A / N)^(1/2)), 'time' by the time step (h = dt).
Reads results/tables/runs.csv, prints one block per quantity and writes
results/tables/gci_<mesh|time>.csv.

Procedure, Celik et al., J. Fluids Eng. 130 (2008) 078001:
  r21 = h2 / h1, r32 = h3 / h2, e21 = phi2 - phi1, e32 = phi3 - phi2,
  s = sign(e32 / e21),
  p = |ln|e32 / e21| + q(p)| / ln r21,  q(p) = ln((r21^p - s) / (r32^p - s)),
  phi_ext = (r21^p phi1 - phi2) / (r21^p - 1),
  e_a = |(phi1 - phi2) / phi1|,  GCI_fine = 1.25 e_a / (r21^p - 1).

Numerical uncertainty used later (u_num, relative to phi1): GCI_fine when
the convergence is monotonic. When it is oscillatory (s < 0) or no order can
be found, Richardson extrapolation does not apply; this project then uses half
the spread of the three solutions, |max - min| / 2 / |phi1|. That fallback is
a choice of this project, not part of the Celik et al. procedure.
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AREA = 3.5 * 2.0 - math.pi * 0.05**2       # m^2, the 2-D domain
QUANTITIES = ["Cd_mean", "Cl_rms", "St", "Cp_base"]


def observed_order(phi, h, tol=1e-12, max_iter=200):
    """Observed order p from three solutions, finest first. Fixed-point iteration."""
    (f1, f2, f3), (h1, h2, h3) = phi, h
    r21, r32 = h2 / h1, h3 / h2
    e21, e32 = f2 - f1, f3 - f2
    if e21 == 0 or e32 == 0:
        return float("nan"), 0
    s = math.copysign(1.0, e32 / e21)
    p = 1.0 / math.log(r21) * abs(math.log(abs(e32 / e21)))
    for _ in range(max_iter):
        q = math.log((r21**p - s) / (r32**p - s))
        p_new = abs(math.log(abs(e32 / e21)) + q) / math.log(r21)
        if abs(p_new - p) < tol:
            return p_new, s
        p = p_new
    return p, s


def gci(phi, h):
    """Observed order, extrapolated value and fine-grid GCI of three solutions."""
    f1, f2, _ = phi
    r21 = h[1] / h[0]
    half_spread = 0.5 * (max(phi) - min(phi)) / abs(f1)
    p, s = observed_order(phi, h)
    out = {"phi1": f1, "phi2": phi[1], "phi3": phi[2],
           "r21": r21, "r32": h[2] / h[1], "p": p,
           "oscillatory": s < 0}
    if math.isnan(p):
        out.update(phi_ext=float("nan"), e_a21=abs((f1 - f2) / f1),
                   e_ext21=float("nan"), gci_fine21=float("nan"), u_num=half_spread)
        return out
    rp = r21**p
    phi_ext = (rp * f1 - f2) / (rp - 1)
    e_a = abs((f1 - f2) / f1)
    out.update(phi_ext=phi_ext, e_a21=e_a,
               e_ext21=abs((phi_ext - f1) / phi_ext),
               gci_fine21=1.25 * e_a / (rp - 1))
    out["u_num"] = half_spread if out["oscillatory"] else out["gci_fine21"]
    return out


def main(argv):
    if len(argv) != 5 or argv[1] not in ("mesh", "time"):
        sys.exit(__doc__)
    import pandas as pd

    kind, runs = argv[1], argv[2:]
    table = pd.read_csv(ROOT / "results" / "tables" / "runs.csv").set_index("run")
    missing = [r for r in runs if r not in table.index]
    if missing:
        sys.exit(f"not analysed yet: {missing}. Run postprocessing/analyze_case.py first.")
    rows = table.loc[runs]
    if kind == "mesh":
        h = [math.sqrt(AREA / n) for n in rows["cells"]]
    else:
        h = list(rows["dt"])
    print(f"{kind} study, finest first: {', '.join(runs)}")
    print("  h = " + ", ".join(f"{x:.4g}" for x in h))
    results = []
    for name in QUANTITIES:
        g = gci(list(rows[name]), h)
        results.append({"quantity": name, **g})
        flag = "  oscillatory" if g["oscillatory"] else ""
        print(f"  {name:8s} phi = {g['phi1']:.5g} {g['phi2']:.5g} {g['phi3']:.5g}"
              f"  p = {g['p']:.3g}  phi_ext = {g['phi_ext']:.5g}"
              f"  e_a21 = {100 * g['e_a21']:.3g} %  GCI_fine = {100 * g['gci_fine21']:.3g} %"
              f"  u_num = {100 * g['u_num']:.3g} %{flag}")
    out = ROOT / "results" / "tables" / f"gci_{kind}.csv"
    pd.DataFrame(results).to_csv(out, index=False, float_format="%.6g")
    print(f"  wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv)