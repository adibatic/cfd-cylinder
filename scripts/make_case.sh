#!/usr/bin/env bash
# Create runs/<run> from the case template, write its mesh and check it.
# Usage: scripts/make_case.sh <coarse|medium|fine> [deltaT]
#   scripts/make_case.sh medium          -> runs/medium,        deltaT 5e-5 s
#   scripts/make_case.sh medium 1e-4     -> runs/medium-dt1e-4, deltaT 1e-4 s
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
source "$ROOT/scripts/foam_env.sh"

level=${1:?usage: make_case.sh <coarse|medium|fine> [deltaT]}
dt=${2:-5e-5}
run=$level
[ "$dt" = 5e-5 ] || run="$level-dt$dt"
dir="$ROOT/runs/$run"
if [ -e "$dir" ]; then
    echo "runs/$run already exists. Remove it first: rm -rf runs/$run" >&2
    exit 1
fi

python3 "$ROOT/mesh/make_blockmesh.py" "$level"
mkdir -p "$ROOT/runs"
cp -r "$ROOT/case" "$dir"
cp "$ROOT/mesh/blockMeshDict.$level" "$dir/system/blockMeshDict"
foamDictionary -entry deltaT -set "$dt" "$dir/system/controlDict" > /dev/null 2>&1

cd "$dir"
blockMesh > log.blockMesh 2>&1
checkMesh > log.checkMesh 2>&1
touch "$run.foam"     # open this file in ParaView
if ! grep -q "Mesh OK" log.checkMesh; then
    echo "checkMesh failed: see runs/$run/log.checkMesh" >&2
    exit 1
fi
cells=$(awk '/^ *cells:/ {print $2; exit}' log.checkMesh)
echo "runs/$run: $cells cells, deltaT $dt s, Mesh OK"