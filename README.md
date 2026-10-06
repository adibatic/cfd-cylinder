# CFD: Circular Cylinder

**Verification and Validation** of CFD Predictions for Flow Around a Circular Cylinder Using OpenFOAM

## Objective

This project investigates the accuracy and numerical sensitivity of CFD predictions for flow around a circular cylinder. It simulates the unsteady flow with OpenFOAM, shows mesh and time-step independence, compares the results with published reference data, and quantifies the error.

## Tools

- OpenFOAM
- ParaView
- Python: NumPy, SciPy, Matplotlib, pandas
- Git and GitHub

## Setup

Requires OpenFOAM (ESI release, tested with v2606) and ParaView:

    curl https://dl.openfoam.com/add-debian-repo.sh | sudo bash
    sudo apt-get update
    sudo apt-get install -y openfoam-default paraview
    echo "source /usr/lib/openfoam/openfoam2606/etc/bashrc" >> ~/.bashrc

Run this one-time if the repo does not exist in your directory yet:
```bash
git clone git@github.com:adibatic/cfd-vv-cylinder.git
cd cfd-vv-cylinder
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run this command every new terminal:
```bash
source .venv/bin/activate
```

## Environment

| Item | Value |
|---|---|
| OS | Ubuntu 22.04.5 LTS |
| CPU | AMD Ryzen 7 6800HS Creator Edition |
| Cores | 16 |
| RAM | 27Gi |
| OpenFOAM | ESI v2606 |
| ParaView | 5.10.0-RC1 |
| Python | 3.14.7 |

## Agent log

| Date | What the agent did wrong | How I caught it | Rule added to CLAUDE.md |
|---|---|---|---|

## Problem

A uniform stream of air flows past a stationary circular cylinder. The cylinder is long, so the flow is modelled in 2-D.

| Symbol | Meaning | Value |
|---|---|---|
| D | cylinder diameter | 0.1 m |
| U | free-stream speed | 10 m/s |
| rho | air density | 1.225 kg/m^3 |
| nu | kinematic viscosity | 1.5e-5 m^2/s |
| Re = UD/nu | Reynolds number | 66,667 |

At this Reynolds number the boundary layer is still laminar when it separates (subcritical regime), the wake is turbulent, and vortices shed at a nearly constant Strouhal number. The drag crisis starts only at Re of about 2e5 to 5e5.

Quantities predicted:

| Quantity | Definition |
|---|---|
| mean drag coefficient | $C_D = F_D / (\tfrac12 \rho U^2 D\,s)$, time-averaged over whole shedding periods |
| rms lift coefficient | $C_{L,rms}$ of $C_L = F_L / (\tfrac12 \rho U^2 D\,s)$ |
| Strouhal number | $St = f D / U$, f from the FFT of $C_L(t)$ |
| pressure coefficient | $C_p(\theta) = (p - p_\infty) / (\tfrac12 \rho U^2)$, time-averaged |

s = 0.01 m is the depth of the 2-D slice; the coefficients do not depend on it.

Time scales: one flow-through of the domain takes 0.35 s, one shedding period about 0.05 s. Each run covers 1.5 s; the first 0.5 s is discarded as start-up, which leaves about 20 periods for statistics.

## Method

- **Equations:** incompressible Navier-Stokes (Mach 0.03), Reynolds-averaged in time (URANS). The vortex shedding is resolved in time; small-scale turbulence is modelled with an eddy viscosity.
- **Turbulence model:** k-omega SST (Menter 1994). It limits the eddy viscosity in adverse pressure gradients, which is where the flow separates.
- **Solver:** OpenFOAM `pimpleFoam` (transient, PIMPLE pressure-velocity coupling).
- **Forces:** pressure and viscous stress integrated over the cylinder every time step (`forceCoeffs`).
- **Verification:** three systematically refined meshes with the grid convergence index (Celik et al. 2008), three time steps, statistical convergence checks.
- **Validation:** comparison of C_D, St, rms C_L and base C_p with published experiments.

Assumptions and their expected effect:

| Assumption | Expected effect |
|---|---|
| 2-D flow | real wake is 3-D; 2-D models usually over-predict mean drag and lift fluctuation |
| URANS k-omega SST | treats the laminar separating boundary layer as turbulent; may shift separation and damp shedding |
| incompressible, constant properties | negligible at Mach 0.03 |
| inflow turbulence about 1 % | real experiments may differ; shifts separation at this Re |
| free-slip side walls, 5 % blockage, no blockage correction | slightly higher speed around the cylinder |
| smooth, stationary cylinder | no roughness or vibration effects |
| small initial cross-flow (0.3 m/s) to trigger shedding | removed by discarding the first 0.5 s |

## Domain

Cylinder centre at the origin, flow in +x.

    y = +1.0  +----------------------------------------------------+  top (symmetryPlane)
              |                +---------+                         |
    inlet     |                |  _---_  |                         |  outlet
    x = -1.0  |                | (  O  ) |   ->  wake  ->  ->      |  x = +2.5
    (U fixed) |                |  -___-  |                         |  (p fixed)
              |                +---------+                         |
    y = -1.0  +----------------------------------------------------+  bottom (symmetryPlane)

| Dimension | Value | In diameters |
|---|---|---|
| cylinder diameter D | 0.1 m | 1 |
| inlet distance from centre | 1.0 m | 10 |
| outlet distance from centre | 2.5 m | 25 |
| domain half height | 1.0 m | 10 |
| depth (one cell, 2-D) | 0.01 m | 0.1 |
| blockage D / height | 5 % | |

| Patch | Type | Location |
|---|---|---|
| inlet | patch | x = -1.0 m |
| outlet | patch | x = +2.5 m |
| top, bottom | symmetryPlane | y = +/-1.0 m |
| cylinder | wall | r = 0.05 m |
| frontAndBack | empty | z = +/-0.005 m (makes the case 2-D) |

Reference values for the force coefficients: U = 10 m/s, rho = 1.225 kg/m^3, lRef = D = 0.1 m, Aref = D x depth = 0.001 m^2.

The mesh is a structured O-grid of 16 blocks: 4 ring blocks around the cylinder (r = 0.05 to 0.075 m, boundary layer), 4 transition blocks to a 0.4 m square box, and 8 outer blocks stretched to the far field. The cells are nearly orthogonal to the wall, small near the cylinder and in the wake, and large far away.

## Progress

- [x] Day 1: install OpenFOAM and ParaView
- [ ] Day 2: physics, geometry, mesh generator, case template, baseline mesh
<!--
- [ ] Day 3: baseline run, flow visualization, residuals, forces
- [ ] Day 4: coarse, medium and fine meshes
- [ ] Day 5-6: mesh study, compare C_D, C_L and St
- [ ] Day 7: time-step study
- [ ] Day 8: C_L(t), FFT, shedding frequency
- [ ] Day 9: reference data and validation
- [ ] Day 10: error analysis and engineering interpretation
- [ ] Day 11-14: final report and GitHub -->
