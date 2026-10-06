"""Checks of the mesh generator that need no OpenFOAM."""
import math

import pytest

import make_blockmesh as mb


def test_geometric_segment_fills_its_length():
    n, expansion = mb.design_segment(0.025, 5e-5, 2.5e-3)
    sizes = mb.cell_sizes(0.025, n, expansion)
    assert sum(sizes) == pytest.approx(0.025, rel=1e-12)
    assert sizes[-1] / sizes[0] == pytest.approx(expansion, rel=1e-12)


def test_uniform_segment():
    assert mb.cell_sizes(0.4, 4, 1.0) == pytest.approx([0.1] * 4)


def test_design_hits_first_and_last_cell_on_medium():
    # rounding the count to an integer moves the sizes a little, not a lot
    n, expansion = mb.design_segment(0.025, 5e-5, 2.5e-3)
    sizes = mb.cell_sizes(0.025, n, expansion)
    assert sizes[0] == pytest.approx(5e-5, rel=0.05)
    assert sizes[-1] == pytest.approx(2.5e-3, rel=0.05)


def test_cylinder_and_ring_points_are_on_their_circles():
    pts = mb.vertices_2d()
    for x, y in pts[:4]:
        assert math.hypot(x, y) == pytest.approx(mb.R, rel=1e-12)
    for x, y in pts[4:8]:
        assert math.hypot(x, y) == pytest.approx(mb.R_RING, rel=1e-12)


def test_every_block_is_counter_clockwise():
    # blockMesh needs right-handed blocks: positive signed area seen from +z
    pts = mb.vertices_2d()
    for quad, _, _ in mb.block_list(mb.design("coarse")):
        xy = [pts[i] for i in quad]
        area = 0.5 * sum(xy[k][0] * xy[(k + 1) % 4][1] - xy[(k + 1) % 4][0] * xy[k][1]
                         for k in range(4))
        assert area > 0


def test_cell_count_matches_blocks():
    for level in mb.LEVELS:
        d = mb.design(level)
        total = sum(cells[0] * cells[1] for _, cells, _ in mb.block_list(d))
        assert total == mb.cell_count(d)


def test_refinement_ratio_is_about_1_5():
    # 2-D: representative cell size h ~ N^(-1/2), so r = (N_fine / N_coarse)^(1/2)
    n = {level: mb.cell_count(mb.design(level)) for level in mb.LEVELS}
    assert (n["medium"] / n["coarse"]) ** 0.5 == pytest.approx(1.5, rel=0.01)
    assert (n["fine"] / n["medium"]) ** 0.5 == pytest.approx(1.5, rel=0.01)


def test_first_cell_shrinks_with_refinement():
    h = [mb.first_cell(mb.design(level)) for level in mb.LEVELS]
    assert h[0] / h[1] == pytest.approx(1.5, rel=0.05)
    assert h[1] / h[2] == pytest.approx(1.5, rel=0.05)


def test_dictionary_has_all_patches():
    text = mb.blockmesh_dict("coarse")
    for name in ("inlet", "outlet", "top", "bottom", "cylinder", "frontAndBack"):
        assert name in text
    assert text.count("arc ") == 16