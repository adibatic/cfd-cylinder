#!/usr/bin/env python3
"""Write the blockMeshDict of the cylinder O-grid for one refinement level.

Usage:
    python3 mesh/make_blockmesh.py coarse       # writes mesh/blockMeshDict.coarse
    python3 mesh/make_blockmesh.py all          # coarse, medium and fine

The mesh has 16 blocks: 4 ring blocks around the cylinder, 4 transition
blocks out to a square box, and 8 outer blocks out to the far field.
The medium level is designed from cell sizes; coarse and fine divide and
multiply every cell count by the refinement ratio and keep every segment's
total expansion, so the three meshes are geometrically similar.
"""
import math
import sys
from pathlib import Path

# Geometry (m), the values in the README Domain section
D = 0.1
R = D / 2           # cylinder radius
R_RING = 0.075      # outer radius of the boundary-layer ring
BOX = 0.2           # half width of the square box around the ring
X_IN = -1.0         # inlet
X_OUT = 2.5         # outlet
H = 1.0             # half height (top and bottom)
DEPTH = 0.01        # one cell thick: 2-D

# Refinement ratio between levels, in each direction
LEVELS = {"coarse": 1 / 1.5, "medium": 1.0, "fine": 1.5}

# Medium design: cells per quarter of the cylinder, and for each radial or
# axial segment (length, first cell, last cell), in metres.
NQ = 32
SEGMENTS = {
    "ring":  (R_RING - R, 5.0e-5, 2.5e-3),     # wall to ring, first cell at the wall
    "trans": (BOX - R_RING, 2.5e-3, 1.25e-2),  # ring to box
    "up":    (-BOX - X_IN, 1.25e-2, 8.0e-2),   # box to inlet
    "side":  (H - BOX, 1.25e-2, 8.0e-2),       # box to top and bottom
    "down":  (X_OUT - BOX, 1.25e-2, 5.0e-2),   # box to outlet: the wake
}

N2 = 24             # points in one z plane: 4 cylinder, 4 ring, 16 grid


# ---------------------------------------------------------------- cell sizes

def design_segment(length, first, last):
    """Cell count and total expansion (last/first) of a geometric segment.

    Cells grow by a constant ratio r from `first` to `last`. The sum of the
    geometric series is length = (r * last - first) / (r - 1), so
    r = (length - first) / (length - last).
    """
    r = (length - first) / (length - last)
    n = 1 + math.log(last / first) / math.log(r)
    return max(1, round(n)), last / first


def cell_sizes(length, n, expansion):
    """The n cell sizes of a segment with total expansion last/first."""
    if n == 1:
        return [length]
    r = expansion ** (1.0 / (n - 1))
    if abs(r - 1.0) < 1e-12:
        return [length / n] * n
    first = length * (r - 1.0) / (r**n - 1.0)
    return [first * r**k for k in range(n)]


def design(level):
    """Cell counts and expansions of every segment at one level."""
    f = LEVELS[level]
    d = {"nq": round(NQ * f)}
    for name, (length, first, last) in SEGMENTS.items():
        n0, expansion = design_segment(length, first, last)
        d[name] = (length, round(n0 * f), expansion)
    return d


def cell_count(d):
    nq, n_ring, n_trans = d["nq"], d["ring"][1], d["trans"][1]
    n_up, n_down, n_side = d["up"][1], d["down"][1], d["side"][1]
    rings = 4 * nq * (n_ring + n_trans)
    columns = n_up + nq + n_down
    rows = n_side + nq + n_side
    return rings + columns * rows - nq * nq


def first_cell(d):
    """Wall-normal height of the first cell on the cylinder (m)."""
    length, n, expansion = d["ring"]
    return cell_sizes(length, n, expansion)[0]


# ---------------------------------------------------------------- geometry

def vertices_2d():
    """24 points in the plane: 4 on the cylinder, 4 on the ring, 16 on a grid."""
    angles = [math.radians(a) for a in (-45.0, 45.0, 135.0, 225.0)]
    cyl = [(R * math.cos(a), R * math.sin(a)) for a in angles]
    ring = [(R_RING * math.cos(a), R_RING * math.sin(a)) for a in angles]
    xs = [X_IN, -BOX, BOX, X_OUT]
    ys = [-H, -BOX, BOX, H]
    grid = [(x, y) for y in ys for x in xs]
    return cyl + ring + grid


def grid_index(i, j):
    """Index of grid point column i, row j (both 0..3)."""
    return 8 + 4 * j + i


# The box corners, in the same order as the cylinder points (-45, 45, 135, 225 deg)
BOX_CORNERS = [grid_index(2, 1), grid_index(2, 2), grid_index(1, 2), grid_index(1, 1)]


def block_list(d):
    """The 16 blocks as (4 in-plane indices, cells, grading).

    Each quad is counter-clockwise seen from +z, so the block is right-handed.
    """
    nq = d["nq"]
    _, n_ring, e_ring = d["ring"]
    _, n_trans, e_trans = d["trans"]
    _, n_up, e_up = d["up"]
    _, n_down, e_down = d["down"]
    _, n_side, e_side = d["side"]
    out = []
    for k in range(4):           # ring and transition blocks: radial direction first
        k1 = (k + 1) % 4
        out.append(((k, 4 + k, 4 + k1, k1), (n_ring, nq), (e_ring, 1)))
        out.append(((4 + k, BOX_CORNERS[k], BOX_CORNERS[k1], 4 + k1),
                    (n_trans, nq), (e_trans, 1)))
    # Outer blocks: x columns (inlet side, box, wake) and y rows (bottom, box, top).
    # Cells are smallest next to the box; grading is last/first in +x and +y.
    columns = [(n_up, 1 / e_up), (nq, 1), (n_down, e_down)]
    rows = [(n_side, 1 / e_side), (nq, 1), (n_side, e_side)]
    g = grid_index
    for j in range(3):
        for i in range(3):
            if (i, j) == (1, 1):
                continue         # the box itself holds the ring and transition blocks
            quad = (g(i, j), g(i + 1, j), g(i + 1, j + 1), g(i, j + 1))
            out.append((quad, (columns[i][0], rows[j][0]), (columns[i][1], rows[j][1])))
    return out


# ---------------------------------------------------------------- dictionary text

def blocks(d):
    lines = []
    for quad, cells, grading in block_list(d):
        ids = list(quad) + [q + N2 for q in quad]
        lines.append("    hex ({}) ({} {} 1) simpleGrading ({:.6g} {:.6g} 1)".format(
            " ".join(str(i) for i in ids), cells[0], cells[1], grading[0], grading[1]))
    return lines


def arcs():
    """Circular edges of the cylinder and the ring, on both z planes."""
    out = []
    for radius, start in ((R, 0), (R_RING, 4)):
        for k in range(4):
            mid = math.radians(90.0 * k)          # halfway between -45 + 90k and 45 + 90k
            for z_off, z in ((0, -DEPTH / 2), (N2, DEPTH / 2)):
                a, b = start + k + z_off, start + (k + 1) % 4 + z_off
                out.append("    arc {} {} ({:.8g} {:.8g} {:.8g})".format(
                    a, b, radius * math.cos(mid), radius * math.sin(mid), z))
    return out


def side_faces(edges):
    """Faces of a side patch: each in-plane edge (a, b) extruded in z."""
    return ["            ({} {} {} {})".format(a, b, b + N2, a + N2) for a, b in edges]


def patches(d):
    g = grid_index
    inlet = [(g(0, j + 1), g(0, j)) for j in range(3)]
    outlet = [(g(3, j), g(3, j + 1)) for j in range(3)]
    bottom = [(g(i, 0), g(i + 1, 0)) for i in range(3)]
    top = [(g(i + 1, 3), g(i, 3)) for i in range(3)]
    cylinder = [((k + 1) % 4, k) for k in range(4)]
    quads = [quad for quad, _, _ in block_list(d)]
    back = ["            ({} {} {} {})".format(q[0], q[3], q[2], q[1]) for q in quads]
    front = ["            ({} {} {} {})".format(*(v + N2 for v in q)) for q in quads]

    def patch(name, kind, lines):
        return "    {}\n    {{\n        type {};\n        faces\n        (\n{}\n        );\n    }}".format(
            name, kind, "\n".join(lines))

    return [
        patch("inlet", "patch", side_faces(inlet)),
        patch("outlet", "patch", side_faces(outlet)),
        patch("top", "symmetryPlane", side_faces(top)),
        patch("bottom", "symmetryPlane", side_faces(bottom)),
        patch("cylinder", "wall", side_faces(cylinder)),
        patch("frontAndBack", "empty", back + front),
    ]


def blockmesh_dict(level):
    d = design(level)
    verts = ["    ({:.8g} {:.8g} {:.8g})".format(x, y, z)
             for z in (-DEPTH / 2, DEPTH / 2) for x, y in vertices_2d()]
    header = (
        "FoamFile\n{\n    version 2.0;\n    format ascii;\n"
        "    class dictionary;\n    object blockMeshDict;\n}\n"
        f"// Generated by mesh/make_blockmesh.py {level}: "
        f"{cell_count(d)} cells, first cell {first_cell(d):.3g} m\n\n"
        "scale 1;\n\n"
    )
    return (header
            + "vertices\n(\n" + "\n".join(verts) + "\n);\n\n"
            + "blocks\n(\n" + "\n".join(blocks(d)) + "\n);\n\n"
            + "edges\n(\n" + "\n".join(arcs()) + "\n);\n\n"
            + "boundary\n(\n" + "\n".join(patches(d)) + "\n);\n")


def main(argv):
    if len(argv) != 2 or argv[1] not in list(LEVELS) + ["all"]:
        sys.exit("usage: make_blockmesh.py <coarse|medium|fine|all>")
    levels = list(LEVELS) if argv[1] == "all" else [argv[1]]
    here = Path(__file__).resolve().parent
    for level in levels:
        d = design(level)
        path = here / ("blockMeshDict." + level)
        path.write_text(blockmesh_dict(level))
        print("{:7s} {:6d} cells  {:3d} around the cylinder  first cell {:.2e} m  -> mesh/{}".format(
            level, cell_count(d), 4 * d["nq"], first_cell(d), path.name))


if __name__ == "__main__":
    main(sys.argv)