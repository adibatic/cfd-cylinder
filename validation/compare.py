#!/usr/bin/env python3
"""Compare the simulation with the reference data.

Usage:
    python3 validation/compare.py --run fine

Reads validation/reference_data.csv (values from sources you have read),
results/tables/runs.csv (the simulation), and the numerical uncertainties in
results/tables/gci_mesh.csv and gci_time.csv; prints the comparison and
writes results/tables/validation.csv.

For each quantity:
  E       = S - D                       comparison error (simulation minus data)
  u_mesh  = u_num of the mesh study     GCI_fine, or half the spread if oscillatory
  u_time  = error of the 5e-5 s step    1.25 |phi(5e-5) - phi_ext| / |phi_ext|,
                                        or half the spread if oscillatory
  U_num   = |S| sqrt(u_mesh^2 + u_time^2)
  U_D     = uncertainty of the data, from the source
  U_val   = sqrt(U_num^2 + U_D^2)
  |E| <= U_val: the difference is within the uncertainties, no model error
                can be shown at this level;
  |E| >  U_val: the difference is a model error of about E.
The u_time formula and the half-spread fallback are choices of this project.
"""
import argparse
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["quantity", "value", "uncertainty", "Re", "source", "location"]


def load_reference(path):
    """Rows of the reference table; every row must name its source."""
    import pandas as pd

    ref = pd.read_csv(path, comment="#")
    missing = [c for c in REQUIRED if c not in ref.columns]
    if missing:
        raise ValueError(f"{path} lacks columns {missing}")
    for _, row in ref.iterrows():
        if not str(row["source"]).strip() or str(row["source"]) == "nan":
            raise ValueError(f"row {row['quantity']} has no source")
        if not str(row["location"]).strip() or str(row["location"]) == "nan":
            raise ValueError(f"row {row['quantity']} has no page, table or figure")
    return ref


def time_uncertainty(row):
    """Relative time error of the middle step (5e-5 s) of the time-step study."""
    if row["oscillatory"] or math.isnan(row["phi_ext"]):
        return row["u_num"]
    return 1.25 * abs(row["phi2"] - row["phi_ext"]) / abs(row["phi_ext"])


def compare(s, d, u_d, u_mesh, u_time=0.0):
    """Comparison error and validation uncertainty of one quantity."""
    e = s - d
    u_num = abs(s) * math.hypot(u_mesh, u_time)
    u_d = 0.0 if math.isnan(u_d) else u_d
    u_val = math.hypot(u_num, u_d)
    return {"S": s, "D": d, "E": e, "E_pct": 100 * e / d,
            "U_num": u_num, "U_D": u_d, "U_val": u_val,
            "within": abs(e) <= u_val}


def main():
    import pandas as pd

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", default="fine")
    args = ap.parse_args()

    tables = ROOT / "results" / "tables"
    ref = load_reference(ROOT / "validation" / "reference_data.csv")
    sim = pd.read_csv(tables / "runs.csv").set_index("run").loc[args.run]
    mesh = pd.read_csv(tables / "gci_mesh.csv").set_index("quantity")
    time = pd.read_csv(tables / "gci_time.csv").set_index("quantity")

    rows = []
    print(f"validation of run {args.run}")
    print(f"  {'quantity':8s} {'S':>8s} {'D':>8s} {'E %':>7s} {'U_num':>7s} {'U_D':>7s} {'U_val':>7s}  verdict      source")
    for _, r in ref.iterrows():
        q = r["quantity"]
        c = compare(float(sim[q]), float(r["value"]), float(r["uncertainty"]),
                    float(mesh.loc[q, "u_num"]), float(time_uncertainty(time.loc[q])))
        verdict = "within" if c["within"] else "model error"
        print(f"  {q:8s} {c['S']:8.4g} {c['D']:8.4g} {c['E_pct']:7.1f} {c['U_num']:7.2g}"
              f" {c['U_D']:7.2g} {c['U_val']:7.2g}  {verdict:12s} {r['source']}, {r['location']}")
        rows.append({"quantity": q, **c, "source": r["source"], "location": r["location"]})
    out = tables / "validation.csv"
    pd.DataFrame(rows).to_csv(out, index=False, float_format="%.6g")
    print(f"  wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
