"""
Unit tests and verification suite for Supersonic and Hypersonic wind tunnel physics.
Validates against NACA 1135 and Anderson Compressible Flow textbook values.
"""

import math
import os
import sys
import numpy as np

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import (
    temp_ratio_isen,
    press_ratio_isen,
    density_ratio_isen,
    area_ratio_isen,
    mach_from_area_ratio,
    normal_shock_mach2,
    normal_shock_press_ratio,
    normal_shock_temp_ratio,
    normal_shock_total_press_ratio,
    calculate_supersonic_tunnel,
    calculate_shock_tube,
    generate_nozzle_contour
)


def test_isentropic_relations():
    M = 2.0
    gamma = 1.4
    t_rat = temp_ratio_isen(M, gamma)
    p_rat = press_ratio_isen(M, gamma)
    rho_rat = density_ratio_isen(M, gamma)
    a_rat = area_ratio_isen(M, gamma)

    assert math.isclose(t_rat, 0.55555555555, rel_tol=1e-5), f"T/T0 failed: {t_rat}"
    assert math.isclose(p_rat, 0.1278045, rel_tol=1e-5), f"P/P0 failed: {p_rat}"
    assert math.isclose(rho_rat, 0.230048, rel_tol=1e-5), f"rho/rho0 failed: {rho_rat}"
    assert math.isclose(a_rat, 1.6875, rel_tol=1e-5), f"A/A* failed: {a_rat}"

    # Inversion
    m_inv_sup = mach_from_area_ratio(a_rat, gamma, supersonic=True)
    assert math.isclose(m_inv_sup, 2.0, rel_tol=1e-5), f"Supersonic inversion failed: {m_inv_sup}"
    m_inv_sub = mach_from_area_ratio(a_rat, gamma, supersonic=False)
    assert 0.3 < m_inv_sub < 0.5, f"Subsonic inversion out of range: {m_inv_sub}"
    print("[PASS] Isentropic flow relations validated.")


def test_normal_shock_relations():
    M1 = 2.0
    gamma = 1.4
    m2 = normal_shock_mach2(M1, gamma)
    p2_p1 = normal_shock_press_ratio(M1, gamma)
    t2_t1 = normal_shock_temp_ratio(M1, gamma)
    p02_p01 = normal_shock_total_press_ratio(M1, gamma)

    assert math.isclose(m2, 0.577350, rel_tol=1e-4), f"M2 failed: {m2}"
    assert math.isclose(p2_p1, 4.5, rel_tol=1e-4), f"P2/P1 failed: {p2_p1}"
    assert math.isclose(t2_t1, 1.6875, rel_tol=1e-4), f"T2/T1 failed: {t2_t1}"
    assert math.isclose(p02_p01, 0.720874, rel_tol=1e-4), f"P02/P01 failed: {p02_p01}"
    print("[PASS] Normal shock relations validated.")


def test_supersonic_blowdown_sizing():
    # 0.1 m x 0.1 m test section at Mach 2.5
    test_area = 0.01  # m^2
    p0_tank = 10.0e5  # 10 bar = 1 MPa
    v_tank = 5.0      # 5 m^3
    res = calculate_supersonic_tunnel(
        mach=2.5,
        test_area=test_area,
        tank_pressure_init=p0_tank,
        tank_volume=v_tank,
        tank_temp_init=300.0,
        back_pressure=101325.0
    )
    assert res.throat_area < res.test_area
    assert res.runtime_adiabatic_to_run > 0.0
    assert res.runtime_adiabatic_to_start > 0.0
    assert res.p0_starting > res.p0_min_running
    assert len(res.time_array) > 100
    print(f"[PASS] Supersonic blow-down tunnel: Throat area={res.throat_area*1e4:.2f} cm^2, Runtime={res.runtime_adiabatic_to_run:.2f} s")


def test_hypersonic_shock_tube():
    # Mach 3.0 shock wave, Helium driver into Air driven
    res = calculate_shock_tube(
        shock_mach=3.0,
        driver_gas="He",
        driven_gas="Air",
        p1=10000.0,
        t1=300.0,
        t4=300.0,
        driver_length=2.0,
        driven_length=8.0
    )
    assert res.p4_over_p1 > 1.0
    assert res.p4 > res.p1
    assert res.w_shock > 0
    assert res.usable_test_window_ms > 0
    assert "Incident Shock" in res.wave_paths
    print(f"[PASS] Hypersonic shock tube: P4/P1={res.p4_over_p1:.2f}, Required P4={res.p4/1e5:.2f} bar, Test window={res.usable_test_window_ms:.2f} ms")


def test_nozzle_contour():
    res = generate_nozzle_contour(mach_design=3.0, test_area=0.04)
    assert res.length_divergent > 0
    assert math.isclose(res.mach_distribution[-1], 3.0, rel_tol=1e-2)
    print(f"[PASS] Nozzle contour generated: Divergent length={res.length_divergent:.3f} m, Theta_max={res.theta_max_deg:.2f} deg")


if __name__ == "__main__":
    test_isentropic_relations()
    test_normal_shock_relations()
    test_supersonic_blowdown_sizing()
    test_hypersonic_shock_tube()
    test_nozzle_contour()
    print("\nALL AERODYNAMIC PHYSICS TESTS PASSED PERFECTLY!")
