#!/usr/bin/env bash
# Load the OpenFOAM environment if it is not already loaded.
# Usage inside other scripts:  source "$ROOT/scripts/foam_env.sh"
if command -v blockMesh >/dev/null 2>&1 && [ -n "${WM_PROJECT_VERSION:-}" ]; then
    return 0 2>/dev/null || exit 0
fi
_foam_rc=$(ls -d /usr/lib/openfoam/openfoam*/etc/bashrc /opt/openfoam*/etc/bashrc \
    "$HOME"/OpenFOAM/OpenFOAM-v*/etc/bashrc 2>/dev/null | sort -V | tail -n 1) || true
if [ -n "$_foam_rc" ]; then
    # OpenFOAM's bashrc is not written for set -e, set -u, or pipefail:
    # switch them off while it runs, then restore the caller's options.
    _foam_flags=$-
    _foam_pipefail=$(shopt -qo pipefail && echo on || echo off)
    set +euo pipefail
    # shellcheck disable=SC1090
    source "$_foam_rc" > /dev/null 2>&1
    [[ $_foam_flags == *e* ]] && set -e
    [[ $_foam_flags == *u* ]] && set -u
    [ "$_foam_pipefail" = on ] && set -o pipefail
fi
if ! command -v blockMesh >/dev/null 2>&1; then
    echo "OpenFOAM environment not found. Install OpenFOAM first (see README)." >&2
    return 1 2>/dev/null || exit 1
fi
unset _foam_rc _foam_flags _foam_pipefail