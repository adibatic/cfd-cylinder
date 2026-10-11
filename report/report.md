# Verification and Validation of CFD Predictions for Flow Around a Circular Cylinder Using OpenFOAM

Author:
Date:

## 1. Abstract

About 150 words: the problem (2-D cylinder, Re = 66,667), the method (OpenFOAM pimpleFoam, URANS k-omega SST), the verification (three meshes and the GCI, three time steps, statistical checks), the validation (comparison with named experiments), and the main finding in one sentence with numbers.

## 2. Introduction

Why the cylinder: the classic bluff-body flow, with separation, shedding, and a turbulent wake, and plenty of experiments. Why verification and validation: a CFD number without its uncertainty is not an engineering result. The questions this project answers.

## 3. Problem

Geometry, flow conditions, Reynolds and Mach numbers, regime, quantities of interest. (README: Problem)

## 4. Method

Equations, turbulence model, solver, schemes, assumptions and their expected effect. (README: Method)

## 5. Domain and mesh

Domain size and boundary conditions; the O-grid; the three meshes and their quality. (README: Domain, Mesh)

## 6. Post-processing

How C_D, C_L, St, and C_p are computed; whole periods; the Hann-windowed spectrum; the statistical convergence checks; the tests against exact answers. (README: Baseline run, Forces, Pressure)

## 7. Verification

7.1 Statistical convergence. 7.2 Mesh study with the GCI. 7.3 Time-step study. 7.4 Summary of numerical uncertainty. (README: Mesh study, Time-step study)

## 8. Validation

Reference data and how they were read; comparison error and validation uncertainty per quantity. (README: Validation)

## 9. Discussion

Sources of model error, in order of likely size; what the comparison can and cannot show; what would be needed to reduce each error. (README: Discussion)

## 10. Working with an AI agent

What the agent was used for (explanation, review, finding bugs), the rules in CLAUDE.md, what it got wrong, and how it was caught. (README: Agent log)

## 11. Limitations

2-D; URANS; one turbulence model; one inflow turbulence level; one domain size; no blockage correction; U_input not estimated; OpenFOAM version.

## 12. Conclusions

Three to five numbered conclusions, each with a number.

## References

The same list as the README References section.
