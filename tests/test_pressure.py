"""Reading OpenFOAM patch values and picking the base pressure."""
import numpy as np
import pytest

import pressure as pr


def test_read_patch_values(tmp_path):
    field = tmp_path / "pMean"
    field.write_text(
        "internalField nonuniform List<scalar> 2 (1 2);\n"
        "boundaryField\n{\n"
        "    inlet\n    {\n        type calculated;\n        value uniform 0.5;\n    }\n"
        "    cylinder\n    {\n        type calculated;\n"
        "        value nonuniform List<scalar> \n3\n(\n-1\n0.25\n2e-1\n)\n;\n    }\n}\n")
    assert pr.read_patch_values(field, "inlet") == pytest.approx([0.5])
    assert pr.read_patch_values(field, "cylinder") == pytest.approx([-1, 0.25, 0.2])


def test_base_pressure_is_the_rear_point():
    theta = np.array([0.0, 90.0, 179.0, 179.5])
    cp = np.array([1.0, -1.0, -0.9, -0.7])
    assert pr.base_pressure(theta, cp) == pytest.approx(-0.8)


def write_field(path, kind, patches):
    """A minimal ASCII field file with nonuniform values on each patch."""
    lines = ["internalField uniform 0;", "boundaryField", "{"]
    for name, values in patches.items():
        if kind == "vector":
            items = "\n".join("(%.10g %.10g %.10g)" % tuple(v) for v in values)
        else:
            items = "\n".join("%.10g" % v for v in values)
        lines += ["    " + name, "    {", "        type calculated;",
                  "        value nonuniform List<%s> %d\n(\n%s\n)\n;" % (kind, len(values), items),
                  "    }"]
    path.write_text("\n".join(lines + ["}"]) + "\n")


def test_potential_flow_gives_one_minus_four_sin_squared(tmp_path):
    # Inviscid flow past a cylinder: p - p_inf = 0.5 U^2 (1 - 4 sin^2 theta),
    # theta measured from the front stagnation point (x = -R, y = 0).
    u, r = 10.0, 0.05
    theta = np.radians(np.arange(2.5, 360, 5.0))
    xyz = np.c_[-r * np.cos(theta), r * np.sin(theta), np.zeros_like(theta)]
    p = 0.5 * u**2 * (1 - 4 * np.sin(theta) ** 2) + 3.0      # p_inf = 3.0
    last = tmp_path / "1.5"
    last.mkdir()
    write_field(last / "pMean", "scalar", {"inlet": [3.0, 3.0], "cylinder": p})
    write_field(last / "C", "vector", {"cylinder": xyz})
    th, cp = pr.pressure_coefficient(tmp_path, u)
    assert cp == pytest.approx(1 - 4 * np.sin(np.radians(th)) ** 2, abs=1e-9)
    assert th.min() >= 0 and th.max() <= 180
    assert pr.base_pressure(th, cp) == pytest.approx(1 - 4 * np.sin(np.radians(177.5)) ** 2)