"""The post-processing reproduces exact answers on made-up signals."""
import numpy as np
import pytest

import analyze_case as ac


def synthetic(f=21.3, cd0=1.4, a_cd=0.05, a_cl=0.9, dt=5e-5, t_end=1.5):
    """C_L oscillates at f, C_D at 2f around cd0, as behind a cylinder."""
    t = np.arange(1, int(round(t_end / dt)) + 1) * dt
    cl = a_cl * np.sin(2 * np.pi * f * t)
    cd = cd0 + a_cd * np.sin(4 * np.pi * f * t)
    return t, cd, cl


def test_upward_crossings_of_a_sine():
    t = np.linspace(0, 1, 100001)
    c = ac.upward_crossings(t, np.sin(2 * np.pi * 5 * t + 0.3))
    assert np.diff(c) == pytest.approx(0.2, abs=1e-6)


def test_peak_frequency_between_fft_bins():
    t, _, cl = synthetic(f=21.3)
    mask, _ = ac.whole_periods(t, cl)
    f, _, _ = ac.peak_frequency(t[mask], cl[mask])
    assert f == pytest.approx(21.3, rel=1e-4)


def test_statistics_recover_the_made_up_values():
    t, cd, cl = synthetic()
    s = ac.statistics(t, cd, cl, t_start=0.5)
    assert s["St"] == pytest.approx(21.3 * 0.1 / 10, rel=1e-4)
    assert s["Cd_mean"] == pytest.approx(1.4, rel=1e-4)
    assert s["Cl_rms"] == pytest.approx(0.9 / np.sqrt(2), rel=1e-4)
    assert s["Cl_amp"] == pytest.approx(0.9, rel=1e-4)
    # upward crossings at t = k / 21.3 for k = 11..31: 21 crossings, 20 whole periods
    assert s["periods"] == 20
    assert s["Cd_half_diff_pct"] < 0.01


def test_drift_fails_the_halves_check():
    t, cd, cl = synthetic()
    cd = cd * (1 + 0.05 * (t - 0.5))     # mean C_D drifts by 5 % over the window
    s = ac.statistics(t, cd, cl, t_start=0.5)
    assert s["Cd_half_diff_pct"] > 1.0


def test_times_rounded_to_six_digits_are_rebuilt():
    # dt = 2.5e-5 s written with 6 significant digits, as OpenFOAM does
    t = 0.5 + 2.5e-5 * np.arange(40000)                    # one second, as in a run
    written = np.array([float("%.6g" % x) for x in t])
    assert np.ptp(np.diff(written)) > 1e-6          # looks uneven
    u = ac.uniform_times(written)
    assert np.diff(u) == pytest.approx(2.5e-5, rel=1e-5)   # St would move in the 6th digit
    assert u == pytest.approx(t, abs=5e-6)                 # the times to the rounding


def test_a_change_of_time_step_is_an_error():
    t = np.r_[np.arange(0, 1, 1e-4), 1 + np.arange(1, 100) * 5e-5]
    with pytest.raises(ValueError, match="not constant"):
        ac.uniform_times(t)


def test_coefficient_file_columns_found_by_name(tmp_path):
    folder = tmp_path / "postProcessing" / "forceCoeffs1" / "0"
    folder.mkdir(parents=True)
    (folder / "coefficient.dat").write_text(
        "# Force and moment coefficients\n"
        "# Time\tCd\tCd(f)\tCd(r)\tCl\tCl(f)\tCl(r)\n"
        "0.1\t1.5\t0\t0\t0.2\t0\t0\n"
        "0.2\t1.6\t0\t0\t-0.2\t0\t0\n")
    t, cd, cl = ac.read_coefficients(tmp_path)
    assert list(t) == [0.1, 0.2]
    assert list(cd) == [1.5, 1.6]
    assert list(cl) == [0.2, -0.2]