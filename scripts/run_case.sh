#!/usr/bin/env bash
# Run pimpleFoam on runs/<run>, in parallel when cores > 1.
# Usage: scripts/run_case.sh <run> <cores>
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
source "$ROOT/scripts/foam_env.sh"

run=${1:?usage: run_case.sh <run> <cores>}
np=${2:-1}
cd "$ROOT/runs/$run"
trap 'echo "run_case.sh: \"$BASH_COMMAND\" failed in runs/$run; see the log.* files there" >&2' ERR
if [ -e log.pimpleFoam ]; then
    echo "runs/$run has already run. Make a fresh case to run it again." >&2
    exit 1
fi

solver_failed() {
    echo "pimpleFoam stopped at $(grep '^Time =' log.pimpleFoam | tail -n 1). See runs/$run/log.pimpleFoam" >&2
    exit 1
}

if [ "$np" -gt 1 ]; then
    foamDictionary -entry numberOfSubdomains -set "$np" system/decomposeParDict > /dev/null 2>&1
    decomposePar > log.decomposePar 2>&1
    mpirun -np "$np" pimpleFoam -parallel > log.pimpleFoam 2>&1 || solver_failed
    reconstructPar > log.reconstructPar 2>&1
    rm -rf processor*
else
    pimpleFoam > log.pimpleFoam 2>&1 || solver_failed
fi
grep -q "^End" log.pimpleFoam || solver_failed
postProcess -func writeCellCentres -latestTime > log.writeCellCentres 2>&1

echo "runs/$run finished: $(grep ExecutionTime log.pimpleFoam | tail -n 1)"