# Verification of CFD Predictions for Flow Around a Circular Cylinder Using OpenFOAM

Author: Adriel
Date: 12 October 2026
Scope: verification. Validation against experiments is not part of this report.

## 1. Abstract

Air at 10 m/s flows past a smooth circular cylinder of diameter 0.1 m (Re = 66,667, subcritical). The unsteady 2-D flow was computed with OpenFOAM v2606 (`pimpleFoam`, URANS with the k-ω SST model) on systematically refined O-grids of 7,578, 17,092, and 38,418 cells, and with three time steps (1e-4, 5e-5, and 2.5e-5 s). Every run sheds vortices regularly, gives at least 23 whole shedding periods, and passes a statistical check (mean drag of the two halves within 0.10 %). The grid convergence index (Celik et al., 2008) and the time-step study give the numerical uncertainty of each result. On the finest mesh the model predicts a Strouhal number St = 0.251 ± 0.004 and a mean drag coefficient C_D = 1.000 ± 0.004, an rms lift coefficient of 0.766 ± 0.023, and a base pressure coefficient of -1.299 ± 0.017; every difference between the two finest meshes and between the two smallest time steps is below 2 %. The report covers verification only: it bounds the numerical error, not the model error, which would need a comparison with experiments.

## 2. Introduction

The circular cylinder in cross-flow is the classic bluff-body flow: the boundary layer separates, the wake becomes unsteady, and vortices shed alternately from the two sides, a von Kármán vortex street. It is also practical: poles, chimneys, cables, and pipes feel a steady drag and an alternating side force at the shedding frequency, which can excite vibration when it approaches a structure's natural frequency.

A computed number is only useful with its uncertainty. This project therefore separates two questions:

1. **Verification:** are the equations solved accurately? How large are the errors from the mesh, the time step, and the finite averaging time?
2. **Validation:** are they the right equations? How far are the verified results from experiments, and what causes the difference?

This report answers the first question. The second is outside its scope; section 8 describes the prepared method.

## 3. Problem

| Symbol | Meaning | Value |
|---|---|---|
| D | cylinder diameter | 0.1 m |
| U | free-stream speed | 10 m/s |
| ρ | air density | 1.225 kg/m³ |
| ν | kinematic viscosity | 1.5e-5 m²/s |
| Re = UD/ν | Reynolds number | 66,667 |
| Ma | Mach number | 0.03 |

At this Reynolds number the flow is subcritical: the boundary layer is laminar when it separates, the wake is turbulent, and the shedding frequency is regular. The quantities of interest are the mean drag coefficient C_D, the rms lift coefficient C_L,rms, the Strouhal number St = fD/U, and the time-averaged pressure coefficient C_p around the cylinder, in particular the base pressure C_p at 180°.

## 4. Method

- **Equations:** incompressible Navier-Stokes, Reynolds-averaged in time (URANS); the shedding is resolved in time and the small-scale turbulence is modelled with an eddy viscosity.
- **Turbulence model:** k-ω SST (Menter, 1994), with wall functions (`nutUSpaldingWallFunction`, `omegaWallFunction`) on a mesh with y⁺ of about 1 at the wall.
- **Solver:** `pimpleFoam` with one outer corrector and two pressure correctors per time step (PISO mode).
- **Schemes:** second-order backward differencing in time; second-order upwind-biased `linearUpwind` for momentum; `limitedLinear` for k and ω; linear gradients and corrected Laplacians.
- **Boundary conditions:** fixed velocity at the inlet with 1 % turbulence intensity and ν_t/ν = 10; fixed pressure and `inletOutlet` velocity at the outlet; symmetry planes at the top and bottom; no slip on the cylinder; `empty` front and back (2-D).
- **Start-up:** a small cross-flow of 0.3 m/s in the initial field triggers shedding; the first 0.5 s (about 1.4 flow-throughs) is discarded, and statistics use t = 0.5 to 1.5 s.

Assumptions and their expected effect:

| Assumption | Expected effect |
|---|---|
| 2-D flow | the real wake is 3-D; 2-D models usually over-predict mean drag and lift fluctuation |
| URANS k-ω SST | treats the laminar separating boundary layer as turbulent; may shift separation and damp shedding |
| incompressible, constant properties | negligible at Ma = 0.03 |
| inflow turbulence about 1 % | experiments differ; shifts separation at this Re |
| 5 % blockage, symmetry side walls, no correction | slightly higher speed past the cylinder, slightly higher forces |

## 5. Domain and mesh

The domain extends 10 D upstream, 25 D downstream, and 10 D to each side (blockage 5 %), one cell deep. The mesh is a structured O-grid of 16 blocks, written by `mesh/make_blockmesh.py`: four ring blocks around the cylinder resolve the boundary layer, four transition blocks lead to a 0.4 m square, and eight outer blocks stretch to the far field.

The three meshes differ only in resolution: every block keeps its expansion ratio and the cell counts scale by 1.5 in each direction, so the meshes are geometrically similar, as the grid convergence index assumes.

| Mesh | Cells | Cells around the cylinder | First cell at the wall | Max non-orthogonality | Max skewness |
|---|---|---|---|---|---|
| coarse | 7,578 | 84 | 7.37e-5 m | 41.9° | 0.50 |
| medium | 17,092 | 128 | 4.98e-5 m | 43.0° | 0.52 |
| fine | 38,418 | 192 | 3.38e-5 m | 43.7° | 0.53 |

All three pass `checkMesh` ("Mesh OK"), and the total volume equals the domain minus the cylinder to six or seven digits, which confirms the curved edges.

![coarse mesh](../results/figures/mesh_coarse.png)

## 6. Post-processing

- **Forces:** `forceCoeffs` integrates pressure and viscous stress over the cylinder every time step.
- **Statistics over whole periods:** `postprocessing/analyze_case.py` keeps only the time between the first and last upward zero crossing of C_L after t = 0.5 s, so no partial period biases the means.
- **Shedding frequency:** the peak of the Hann-windowed spectrum of C_L, refined between FFT bins, and checked against the zero-crossing frequency (the two agree to 0.0013 Hz on the medium mesh).
- **Pressure:** `postprocessing/pressure.py` computes the time-averaged C_p from `pMean` around the cylinder, with p_∞ the mean pressure on the inlet; C_p = 1.00 at the front stagnation point confirms the reference.
- **Tests:** every analysis function is checked against signals and fields with exact answers (`pytest`: 30 tests pass).

The medium baseline run (8 cores, 15.5 minutes) finished cleanly: no `nan`, no bounding after the start-up, a maximum Courant number of 0.75 after the start-up, and a mean y⁺ of 1.0 on the cylinder. The wake sheds a regular vortex street:

![vorticity, medium mesh](../results/figures/vorticity_medium_paraview.png)

The mean pressure follows potential flow on the front of the cylinder, reaches its minimum of -2.05 at 77° instead of -3 at 90°, and stays nearly constant behind separation; this base suction is the main source of drag.

![C_p on the medium mesh](../results/figures/medium_cp.png)

## 7. Verification

### 7.1 Statistical convergence

Every run covers at least 23 whole shedding periods (requirement: 15). The mean C_D of the first and second halves of the averaging window differs by at most 0.10 % (requirement: 1 %). The statistical uncertainty is therefore small compared with the discretization errors below.

### 7.2 Mesh study

| Mesh | St | mean C_D | rms C_L | base C_p |
|---|---|---|---|---|
| coarse | 0.2388 | 1.022 | 0.792 | -1.314 |
| medium | 0.2473 | 1.003 | 0.754 | -1.283 |
| fine | 0.2512 | 1.000 | 0.766 | -1.299 |

Grid convergence index after Celik et al. (2008), with h = (A/N)^½ and refinement ratios r₂₁ = 1.499, r₃₂ = 1.502:

| Quantity | Convergence | Observed order p | Fine vs medium | Uncertainty used |
|---|---|---|---|---|
| St | monotonic | 1.92 | 1.54 % | 1.63 % (GCI) |
| mean C_D | monotonic | 3.78 | 0.39 % | 0.14 % (GCI); 0.39 % quoted as the conservative figure |
| rms C_L | oscillatory | - | 1.64 % | 2.5 % (half the spread) |
| base C_p | oscillatory | - | 1.20 % | 1.2 % (half the spread) |

St converges at close to the formal second order. For C_D the observed order of 3.8 is far above the schemes' order of 2, a sign that the coarse mesh is outside the asymptotic range; the fine-medium difference is therefore quoted as a conservative bound. rms C_L and base C_p converge oscillatorily, where the GCI does not apply; for them half the spread of the three results is used, a project choice. Every fine-medium difference is below 2 %.

The study stops at three meshes. In the reference runs of the guide this project followed, a fourth, extra-fine mesh (86,956 cells) was unstable at Δt = 5e-5 s (Courant number about 1.6 with one PISO pass), and at Δt = 2.5e-5 s its forces carried bursts of high-frequency noise from shear-layer vortices that the URANS model leaves undamped; it was not repeated in this project.

### 7.3 Time-step study

On the medium mesh, with Δt = 1e-4, 5e-5, and 2.5e-5 s:

| Quantity | 1e-4 s | 5e-5 s | 2.5e-5 s | Observed order | 5e-5 s off the extrapolated value |
|---|---|---|---|---|---|
| mean C_D | 1.0190 | 1.0035 | 1.0008 | 2.5 | 0.32 % |
| rms C_L | 0.7843 | 0.7536 | 0.7464 | 2.1 | 1.27 % |
| base C_p | -1.3263 | -1.2831 | -1.2778 | 3.0 | 0.47 % |
| St | 0.2474 | 0.2473 | 0.2479 | oscillatory | below 0.3 % |

The observed orders, 2.1 to 3.0, are at or above the second order of the backward scheme. The largest step runs stably at a Courant number of about 1.5 but misses rms C_L by 5 %: stable is not the same as accurate. The step used for the mesh study, 5e-5 s, is within 2 % of the extrapolated value for every quantity.

### 7.4 Numerical uncertainty

The mesh and time uncertainties are independent and are added in quadrature, U_num = (u_mesh² + u_time²)^½, with u_time = 1.25 times the distance of the 5e-5 s result from the extrapolated value (a project choice mirroring the GCI safety factor).

| Quantity | Fine-mesh result | U_num |
|---|---|---|
| St | 0.2512 | ± 0.0041 (1.6 %) |
| mean C_D | 1.000 | ± 0.004 (0.4 %) |
| rms C_L | 0.766 | ± 0.023 (3.0 %) |
| base C_p | -1.299 | ± 0.017 (1.3 %) |

## 8. Validation

`validation/compare.py` compares each fine-mesh result S with an experimental value D: the comparison error E = S - D, and the validation uncertainty U_val = (U_num² + U_D²)^½, a simplified form of ASME V&V 20 that leaves out the input uncertainty U_input. If |E| ≤ U_val, no model error can be shown at this level of uncertainty; if |E| is larger, the difference is model error.

**Not performed.** The method above is implemented and tested, but no experimental values have been added: they enter `validation/reference_data.csv` only from sources the author has read, each with its location in the source, and a test rejects any row without a source. No comparison is therefore reported, and the results of this report should not be read as a statement of how well the model matches real flow.

## 9. Discussion

The numerical error is small and known: at most 3 % (rms C_L), and below 0.5 % for mean C_D. Any larger difference from experiments would therefore come from the model, not from the numerics. The likely contributions, which no mesh or time-step study can detect because they are the same on every mesh:

1. **2-D instead of 3-D.** The computed vortices are perfectly coherent along the span; real ones are not. 2-D models usually over-predict mean drag and rms lift for this reason.
2. **The turbulence model.** SST treats the laminar separating boundary layer as turbulent wherever there is eddy viscosity, which can delay separation.
3. **Inflow turbulence.** The 1 % set at the inlet decays before it reaches the cylinder; wind tunnels differ, and at this Re the turbulence level shifts separation.
4. **Blockage.** 5 % blockage without correction speeds up the flow past the cylinder and raises the forces slightly.

Their size is not estimated here. Only a comparison with experiments can show which of them dominate, and how far the verified model can be used: for the shedding frequency, the mean drag, and the fluctuating lift.

## 10. Working with an AI agent

The project was built with Claude Code under written rules in `CLAUDE.md`: reference values and equations only from sources the author has read, no change to physical parameters without saying so, checks that must pass before a result is used, and no files changed or committed without an explicit request. The agent wrote the step-by-step guide that the project followed, explained concepts, reviewed results, and found bugs. Near the end, at the author's request, it also generated the remaining code (validation, figures, animation), the README front page, and a first draft of this report from the project's own result tables; the author reviewed them.

Errors made by the agent and caught during the project:

- **A silent script failure.** The OpenFOAM environment loader stopped any script that runs with `set -e`, with no message, whenever OpenFOAM was not already loaded in the terminal. Found when a run exited after 0.2 s; fixed by switching those options off while OpenFOAM's own setup runs.
- **A broken speed test.** A short benchmark run never wrote a time folder, because its write interval was longer than the run, so the reconstruction step failed. Found from the missing output; fixed by setting both values.
- **Numbers that were not the author's own.** Several README tables still held values from the agent's reference run on another machine. Found by comparing them with the project's own result tables, and recomputed from those.
- **A wrong explanation.** The guide claimed the coarse mesh's larger aspect ratio reflected more stretched cells; in fact checkMesh measures 2-D cells along the x and y axes. Found by questioning an unintuitive number.

## 11. Limitations

- 2-D only; URANS with a single turbulence model (k-ω SST).
- One inflow turbulence level, one domain size, no blockage correction.
- The input uncertainty U_input is not estimated.
- No validation: the model error, the difference from real flow, is not known.
- The runs used OpenFOAM v2606 on one machine; another version or core count changes the last digits.

## 12. Conclusions

1. On three systematically refined meshes, St and mean C_D converge monotonically: St at an observed order of 1.9, close to the schemes' formal second order.
2. The fine-mesh results carry a numerical uncertainty of 1.6 % (St), 0.4 % (mean C_D), 3.0 % (rms C_L), and 1.3 % (base C_p); every fine-medium and every smallest-time-step difference is below 2 %.
3. The verified model predicts St = 0.251 ± 0.004 and mean C_D = 1.000 ± 0.004 at Re = 66,667.
4. A larger time step (1e-4 s) is stable but misses rms C_L by 5 %: stability does not imply accuracy.
5. Because the numerical error is small and known, a future comparison with experiments would measure the model error directly; `validation/compare.py` is prepared for it.

## References

- Celik, I. B., Ghia, U., Roache, P. J., Freitas, C. J., Coleman, H., & Raad, P. E. (2008). Procedure for estimation and reporting of uncertainty due to discretization in CFD applications. Journal of Fluids Engineering, 130(7), 078001.
- Menter, F. R. (1994). Two-equation eddy-viscosity turbulence models for engineering applications. AIAA Journal, 32(8), 1598-1605.
