# Project rules

Cylinder CFD verification and validation: OpenFOAM (ESI v2606), Python, Re = 66,667.
Mesh generator in mesh/, case template in case/, scripts in scripts/, analysis in
postprocessing/, verification/ and validation/, tests in tests/.

## Units and numbers
- SI units everywhere. D = 0.1 m, U = 10 m/s, nu = 1.5e-5 m^2/s, rho = 1.225 kg/m^3.
- Never change D, U, nu, mesh counts or time steps without saying so in the commit message.
- Reference values (validation/reference_data.csv) must come from a source I have read. Never invent or "recall" a value.
- Equations and model constants must come from a source I have read (a cited paper or the OpenFOAM documentation). Never invent or "recall" one.

## Commands
- Activate: source .venv/bin/activate
- Tests: pytest
- Mesh: python3 mesh/make_blockmesh.py all
- Case: scripts/make_case.sh <coarse|medium|fine> [deltaT]
- Run: scripts/run_case.sh <run> <cores>
- Analyse: python3 postprocessing/analyze_case.py --run <run> --t-start 0.5
- Mesh study: python3 verification/gci.py mesh fine medium coarse
- Time-step study: python3 verification/gci.py time medium-dt2.5e-5 medium medium-dt1e-4
- Validate: python3 validation/compare.py --run fine

## Checks that must pass before a result is used
- pytest passes.
- checkMesh ends with "Mesh OK".
- At least 15 shedding periods, C_D first-vs-second-half difference below 1 %.
- Mesh and time-step studies show differences below 2 % before validating.

## Workflow
- I build this project step by step and type every file myself. Explain, review, and find bugs. Do not create or edit files unless I ask for it in that message.
- Do not commit or push unless I ask. If a request is ambiguous ("proceed", "go ahead"), ask what I mean before changing anything.
- Commits follow Conventional Commits 1.0.0 (feat, fix, perf, style, test, docs, build, ci, chore).
- runs/ is never committed.
- Explain every change you make and why. Do not edit the OpenFOAM case in case/ unless I ask.
