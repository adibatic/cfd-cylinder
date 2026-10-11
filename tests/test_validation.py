"""The validation arithmetic, and the rule that every reference value has a source."""
import math

import pytest

import compare


def test_difference_within_uncertainty():
    c = compare.compare(s=1.30, d=1.25, u_d=0.05, u_mesh=0.02)
    assert c["E"] == pytest.approx(0.05)
    assert c["U_num"] == pytest.approx(0.026)
    assert c["U_val"] == pytest.approx(math.hypot(0.026, 0.05))
    assert c["within"]


def test_difference_larger_than_uncertainty_is_a_model_error():
    c = compare.compare(s=1.60, d=1.25, u_d=0.05, u_mesh=0.01)
    assert c["E_pct"] == pytest.approx(28.0)
    assert not c["within"]


def test_mesh_and_time_uncertainty_add_in_quadrature():
    c = compare.compare(s=2.0, d=2.0, u_d=0.0, u_mesh=0.03, u_time=0.04)
    assert c["U_num"] == pytest.approx(2.0 * 0.05)


def test_time_uncertainty_of_the_middle_step():
    row = {"oscillatory": False, "phi_ext": 1.0, "phi2": 1.004, "u_num": 0.001}
    assert compare.time_uncertainty(row) == pytest.approx(1.25 * 0.004)
    row["oscillatory"] = True
    assert compare.time_uncertainty(row) == pytest.approx(0.001)


def test_reference_row_without_source_is_rejected(tmp_path):
    f = tmp_path / "ref.csv"
    f.write_text("quantity,value,uncertainty,Re,source,location\nSt,0.2,0.01,6e4,,Fig. 3\n")
    with pytest.raises(ValueError, match="no source"):
        compare.load_reference(f)


def test_reference_file_in_repository_is_complete():
    path = compare.ROOT / "validation" / "reference_data.csv"
    if not path.exists():
        pytest.skip("validation/reference_data.csv not written yet")
    compare.load_reference(path)
