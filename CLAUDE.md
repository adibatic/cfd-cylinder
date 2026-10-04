# Project rules

Cylinder CFD verification and validation: OpenFOAM (ESI v2606), Python, Re = 66,667.

## Units and numbers
- SI units everywhere. D = 0.1 m, U = 10 m/s, nu = 1.5e-5 m^2/s, rho = 1.225 kg/m^3.
- Never change D, U, nu, mesh counts or time steps without saying so in the commit message.
- Reference values (validation/reference_data.csv) must come from a source I have read. Never invent or "recall" a value.

## Commands
- Tests: pytest
- Mesh: python3 mesh/make_blockmesh.py all
- Case: scripts/make_case.sh <coarse|medium|fine>
- Run: scripts/run_case.sh <run> <cores>
- Analyse: python3 postprocessing/analyze_case.py --run <run> --t-start 0.5

## Checks that must pass before a result is used
- pytest passes.
- checkMesh ends with "Mesh OK".
- At least 15 shedding periods, C_D first-vs-second-half difference below 1 %.
- Mesh and time-step studies show differences below 2 % before validating.

## Workflow
- Commits follow Conventional Commits (feat, fix, docs, test, build, chore).
- runs/ is never committed.
- Explain every change you make and why. Do not edit the OpenFOAM case in case/ unless I ask.