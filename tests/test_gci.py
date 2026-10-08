"""The GCI recovers the exact order and limit of made-up converging solutions."""
import pytest

import gci


def solutions(phi0, c, p, h):
    return [phi0 + c * x**p for x in h]


def test_constant_ratio_second_order():
    h = [1.0, 1.5, 2.25]
    g = gci.gci(solutions(1.2, 0.03, 2.0, h), h)
    assert g["p"] == pytest.approx(2.0, rel=1e-10)
    assert g["phi_ext"] == pytest.approx(1.2, rel=1e-10)
    assert not g["oscillatory"]


def test_unequal_ratios_need_the_iteration():
    h = [1.0, 1.5, 2.1]                  # r21 = 1.5, r32 = 1.4
    g = gci.gci(solutions(0.21, -0.004, 1.6, h), h)
    assert g["p"] == pytest.approx(1.6, rel=1e-8)
    assert g["phi_ext"] == pytest.approx(0.21, rel=1e-8)


def test_gci_is_the_extrapolated_error_times_1_25():
    # with the exact order, e_ext / e_a = 1 / (r^p - 1) relative to phi_ext
    h = [1.0, 2.0, 4.0]
    g = gci.gci(solutions(1.0, 0.01, 2.0, h), h)
    assert g["gci_fine21"] == pytest.approx(1.25 * g["e_a21"] / 3.0)
    assert g["e_ext21"] == pytest.approx(0.01 / 1.0, rel=1e-10)


def test_oscillatory_convergence_is_flagged():
    h = [1.0, 1.5, 2.25]
    g = gci.gci([1.00, 1.02, 0.99], h)
    assert g["oscillatory"]
    # Richardson does not apply: u_num falls back to half the spread
    assert g["u_num"] == pytest.approx(0.5 * (1.02 - 0.99) / 1.00)


def test_monotonic_u_num_is_the_gci():
    h = [1.0, 1.5, 2.25]
    g = gci.gci(solutions(1.2, 0.03, 2.0, h), h)
    assert g["u_num"] == g["gci_fine21"]


def test_equal_solutions_give_no_order():
    g = gci.gci([1.0, 1.0, 1.1], [1.0, 1.5, 2.25])
    assert g["p"] != g["p"]              # NaN: no error to measure on the two finest