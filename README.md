# CFD Verification & Validation: Flow Around a Circular Cylinder

Verification and Validation of CFD Predictions for Flow Around a Circular Cylinder Using OpenFOAM

## Objective

This project investigates the accuracy and numerical sensitivity of CFD predictions for flow around a circular cylinder. It simulates the unsteady flow with OpenFOAM, shows mesh and time-step independence, compares the results with published reference data, and quantifies the error.

## Tools

- OpenFOAM
- ParaView
- Python: NumPy, SciPy, Matplotlib, pandas
- Git and GitHub

## Setup

```bash
git clone git@github.com:adibatic/cylinder-cfd-vv.git
cd cylinder-cfd-vv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run `source .venv/bin/activate` in every new terminal before running the Python scripts.

## Progress

- [ ] Day 1: install OpenFOAM, run the official tutorial, record the environment
- [ ] Day 2: physics, geometry, mesh generator, case template, baseline mesh
- [ ] Day 3: baseline run, flow visualization, residuals, forces
- [ ] Day 4: coarse, medium and fine meshes
- [ ] Day 5-6: mesh study, compare C_D, C_L and St
- [ ] Day 7: time-step study
- [ ] Day 8: C_L(t), FFT, shedding frequency
- [ ] Day 9: reference data and validation
- [ ] Day 10: error analysis and engineering interpretation
- [ ] Day 11-14: final report and GitHub
