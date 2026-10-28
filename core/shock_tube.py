"""
Hypersonic Shock Tube Module
----------------------------
Implements the fundamental shock tube equation, intermediate states 1-5,
wave speed kinematics, driver/driven sizing, test window duration estimation,
and full x-t wave diagram coordinates.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import numpy as np
from scipy.optimize import brentq

from .gas_dynamics import (
    get_gas,
    GasProperties
)


@dataclass
class ShockTubeResult:
    # Inputs echoed
    shock_mach: float            # Ms
    driver_gas: str
    driven_gas: str
    p1: float                    # Pa
    t1: float                    # K
    t4: float                    # K
    driver_length: float         # m
    driven_length: float         # m
    test_position: float         # m (from diaphragm x=0)

    # Pressures and ratios
    p4_over_p1: float            # Diaphragm pressure ratio
    p4: float                    # Required driver pressure (Pa)
    ms_limit: float              # Theoretical maximum shock Mach for gas pair

    # Wave speeds
    a1: float                    # Driven sound speed (m/s)
    a4: float                    # Driver sound speed (m/s)
    w_shock: float               # Incident shock speed (m/s)
    u2: float                    # Induced flow velocity (m/s)
    w_reflected: float           # Reflected shock velocity (m/s)
    v_exp_head: float            # Expansion fan head speed (-a4, m/s)
    v_exp_tail: float            # Expansion fan tail speed (u3 - a3, m/s)

    # States
    # State 1 (Driven quiescent)
    rho1: float                  # kg/m^3
    # State 2 (Behind incident shock)
    p2: float                    # Pa
    t2: float                    # K
    rho2: float                  # kg/m^3
    a2: float                    # m/s
    m2: float                    # Flow Mach number
    # State 3 (Expanded driver)
    p3: float                    # Pa (= p2)
    t3: float                    # K
    rho3: float                  # kg/m^3
    a3: float                    # m/s
    u3: float                    # m/s (= u2)
    # State 4 (Driver quiescent)
    rho4: float                  # kg/m^3
    # State 5 (Behind reflected shock at end wall)
    p5: float                    # Pa
    t5: float                    # K
    rho5: float                  # kg/m^3
    a5: float                    # m/s
    mr: float                    # Reflected shock Mach number relative to region 2

    # Timing and test windows
    time_shock_arrival: float    # s (incident shock arrives at test position)
    time_contact_arrival: float  # s (contact surface arrives at test position)
    time_expansion_reflect: float# s (expansion fan reflects off driver wall)
    time_expansion_arrival: float# s (reflected expansion wave reaches test position)
    usable_test_window_ms: float # ms (time before contamination / expansion arrival)
    test_limiting_factor: str    # 'Contact Surface' or 'Reflected Expansion Wave'

    # Sizing recommendations
    optimum_driver_length: float # m (minimum driver length to avoid expansion cutoff)
    optimum_length_ratio: float  # L4 / L1

    # Wave paths for x-t diagram
    wave_paths: Dict[str, Tuple[np.ndarray, np.ndarray]] = field(default_factory=dict)


def calc_shock_tube_p4_p1(
    Ms: float,
    gamma1: float,
    R1: float,
    T1: float,
    gamma4: float,
    R4: float,
    T4: float
) -> float:
    """
    Evaluates diaphragm pressure ratio P4/P1 from the classic shock tube relation:
    P4/P1 = [ (2*gamma1*Ms^2 - (gamma1 - 1)) / (gamma1 + 1) ] *
            [ 1 - ((gamma4 - 1)/(gamma1 + 1)) * (a1 / a4) * (Ms - 1/Ms) ]^(-2*gamma4 / (gamma4 - 1))
    """
    a1 = math.sqrt(gamma1 * R1 * T1)
    a4 = math.sqrt(gamma4 * R4 * T4)

    term1 = (2.0 * gamma1 * (Ms ** 2) - (gamma1 - 1.0)) / (gamma1 + 1.0)
    bracket = 1.0 - ((gamma4 - 1.0) / (gamma1 + 1.0)) * (a1 / a4) * (Ms - (1.0 / Ms))

    if bracket <= 1e-6:
        raise ValueError(
            f"Shock Mach {Ms:.2f} is higher than theoretical maximum for gas pair. "
            f"Expansion term <= 0. Driver gas sound speed a4 must be increased (heat driver or use He/H2)."
        )

    exp_term = -2.0 * gamma4 / (gamma4 - 1.0)
    return term1 * (bracket ** exp_term)


def theoretical_max_shock_mach(
    gamma1: float,
    R1: float,
    T1: float,
    gamma4: float,
    R4: float,
    T4: float
) -> float:
    """
    Computes theoretical maximum shock Mach number as P4/P1 -> infinity:
    Ms - 1/Ms = ((gamma1 + 1) / (gamma4 - 1)) * (a4 / a1)
    """
    a1 = math.sqrt(gamma1 * R1 * T1)
    a4 = math.sqrt(gamma4 * R4 * T4)
    beta = ((gamma1 + 1.0) / (gamma4 - 1.0)) * (a4 / a1)
    # Ms^2 - beta*Ms - 1 = 0
    return 0.5 * (beta + math.sqrt(beta ** 2 + 4.0))


def calculate_shock_tube(
    shock_mach: float,
    driver_gas: str = "He",
    driven_gas: str = "Air",
    p1: float = 10000.0,         # 10 kPa
    t1: float = 300.0,           # 300 K
    t4: float = 300.0,           # 300 K
    driver_length: float = 3.0,  # 3 meters
    driven_length: float = 9.0,  # 9 meters
    test_position: Optional[float] = None
) -> ShockTubeResult:
    """
    Solves hypersonic shock tube / shock tunnel gas dynamics, sizing, and run duration.

    Parameters
    ----------
    shock_mach : float
        Target incident shock Mach number (Ms > 1.0)
    driver_gas : str
        Driver gas ('He', 'N2', 'H2', 'Air')
    driven_gas : str
        Driven gas ('Air', 'N2', 'CO2')
    p1 : float
        Initial driven gas pressure (Pa)
    t1 : float
        Initial driven gas temperature (K)
    t4 : float
        Initial driver gas temperature (K)
    driver_length : float
        Length of driver chamber L4 (m), x in [-L4, 0]
    driven_length : float
        Length of driven tube L1 (m), x in [0, L1]
    test_position : float, optional
        Location of test model / pressure sensors (m from diaphragm). Defaults to end-wall L1.

    Returns
    -------
    ShockTubeResult with all wave speeds, states 1-5, and usable test duration.
    """
    if shock_mach <= 1.0001:
        raise ValueError(f"Shock Mach number must be > 1.0 (given {shock_mach})")
    if p1 <= 0 or t1 <= 0 or t4 <= 0 or driver_length <= 0 or driven_length <= 0:
        raise ValueError("Pressures, temperatures, and lengths must be positive.")

    gas1 = get_gas(driven_gas)
    gas4 = get_gas(driver_gas)

    gamma1, R1 = gas1.gamma, gas1.R
    gamma4, R4 = gas4.gamma, gas4.R

    a1 = math.sqrt(gamma1 * R1 * t1)
    a4 = math.sqrt(gamma4 * R4 * t4)
    rho1 = p1 / (R1 * t1)

    # Theoretical maximum shock Mach number limit
    ms_limit = theoretical_max_shock_mach(gamma1, R1, t1, gamma4, R4, t4)
    if shock_mach >= ms_limit:
        raise ValueError(
            f"Requested shock Mach number Ms={shock_mach:.3f} exceeds theoretical ceiling "
            f"Ms_limit={ms_limit:.3f} for {driver_gas} driving {driven_gas} at T1={t1}K, T4={t4}K. "
            f"Consider using a lighter driver gas (e.g. He/H2) or preheating the driver gas."
        )

    # 1. Diaphragm pressure ratio P4/P1
    p4_over_p1 = calc_shock_tube_p4_p1(shock_mach, gamma1, R1, t1, gamma4, R4, t4)
    p4 = p1 * p4_over_p1
    rho4 = p4 / (R4 * t4)

    # 2. State 2: Region behind incident shock
    p2_over_p1 = 1.0 + (2.0 * gamma1 / (gamma1 + 1.0)) * (shock_mach ** 2 - 1.0)
    p2 = p1 * p2_over_p1

    t2_over_t1 = p2_over_p1 * ((2.0 + (gamma1 - 1.0) * (shock_mach ** 2)) / ((gamma1 + 1.0) * (shock_mach ** 2)))
    t2 = t1 * t2_over_t1
    rho2 = p2 / (R1 * t2)
    a2 = math.sqrt(gamma1 * R1 * t2)

    # Induced flow velocity u2
    u2 = (2.0 * a1 / (gamma1 + 1.0)) * (shock_mach - (1.0 / shock_mach))
    m2 = u2 / a2

    # 3. State 3: Region behind contact surface in expanded driver gas
    p3 = p2
    u3 = u2
    # Isentropic expansion from State 4:
    t3 = t4 * ((p3 / p4) ** ((gamma4 - 1.0) / gamma4))
    rho3 = p3 / (R4 * t3)
    a3 = math.sqrt(gamma4 * R4 * t3)

    # 4. State 5: Region behind reflected shock at end wall (x = L1)
    # Gas comes to rest: u5 = 0
    p5_over_p2 = ((gamma1 + 1.0) / (gamma1 - 1.0) + 2.0 - (p1 / p2)) / (1.0 + ((gamma1 + 1.0) / (gamma1 - 1.0)) * (p1 / p2))
    p5 = p2 * p5_over_p2

    t5_over_t2 = p5_over_p2 * ((((gamma1 + 1.0) / (gamma1 - 1.0)) + p5_over_p2) / (1.0 + ((gamma1 + 1.0) / (gamma1 - 1.0)) * p5_over_p2))
    t5 = t2 * t5_over_t2
    rho5 = p5 / (R1 * t5)
    a5 = math.sqrt(gamma1 * R1 * t5)

    # Reflected shock velocity relative to tube:
    rho_ratio_52 = (1.0 + ((gamma1 + 1.0) / (gamma1 - 1.0)) * p5_over_p2) / (((gamma1 + 1.0) / (gamma1 - 1.0)) + p5_over_p2)
    w_reflected = u2 / max(rho_ratio_52 - 1.0, 1e-6)
    mr = (w_reflected + u2) / a2

    # 5. Wave Speeds
    w_shock = shock_mach * a1
    v_exp_head = -a4
    v_exp_tail = u3 - a3

    # Default test position to end-wall if not provided
    if test_position is None or test_position <= 0.0:
        test_position = driven_length
    test_position = min(test_position, driven_length)

    # 6. Timing and Usable Testing Window
    # Time incident shock reaches test position:
    t_shock_arr = test_position / w_shock

    # Time contact surface reaches test position:
    t_cs_arr = test_position / u2 if u2 > 0 else float('inf')

    # Time expansion head reaches driver back wall (x = -driver_length):
    t_exp_back = driver_length / a4

    # Trajectory of reflected expansion wave:
    # After reflecting at x = -L4 at t = t_exp_back, the head of the reflected expansion wave
    # propagates rightward through the expansion fan with characteristic speed dx/dt = u + a.
    # In simple centered expansion fan where u + 2/(gamma4-1)*a = 2/(gamma4-1)*a4:
    # Analytical arrival of reflected expansion wave at diaphragm x=0:
    exp_factor = (gamma4 + 1.0) / (2.0 * (gamma4 - 1.0))
    # Time it emerges from expansion fan tail into region 3:
    t_emerge_tail = t_exp_back * ((a4 / a3) ** ((gamma4 + 1.0) / (gamma4 - 1.0)))

    # In region 3 and region 2, the wave travels at speed u2 + a3 (or u2 + a2).
    # Approximate arrival time of reflected expansion wave at test position:
    speed_in_flow = u2 + a2
    t_exp_arr = t_emerge_tail + (test_position / speed_in_flow)

    # Usable test duration is interval between shock arrival and arrival of either:
    # 1. Contact surface (cold driver gas contaminates test section)
    # 2. Reflected expansion wave (stagnation pressure drops)
    time_limit = min(t_cs_arr, t_exp_arr)
    test_window_s = max(0.0, time_limit - t_shock_arr)
    test_window_ms = test_window_s * 1000.0

    limiting_factor = "Contact Surface (Driver Gas)" if t_cs_arr <= t_exp_arr else "Reflected Expansion Wave"

    # Optimum driver length sizing to prevent premature expansion cutoff:
    # We want t_exp_arr >= t_cs_arr so that driver contamination is the sole boundary:
    # L4_opt = driven_length * ratio_opt
    time_cs_end = driven_length / u2
    # L4_opt such that t_emerge_tail + driven_length/(u2 + a2) = time_cs_end:
    delta_t_req = max(0.0, time_cs_end - (driven_length / speed_in_flow))
    expansion_factor = (a4 / a3) ** ((gamma4 + 1.0) / (gamma4 - 1.0))
    l4_opt = (delta_t_req * a4) / max(expansion_factor, 1e-4)
    length_ratio_opt = l4_opt / driven_length

    # 7. Generate x-t wave paths for plotting
    # Time ceiling for plot
    t_end = max(driven_length / w_shock * 2.5, t_cs_arr * 1.5, t_exp_arr * 1.2, 0.02)
    num_pts = 200

    wave_paths: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}

    # Path 1: Incident Shock: (0, 0) -> (driven_length, driven_length / w_shock)
    t_shock_end = driven_length / w_shock
    wave_paths["Incident Shock"] = (
        np.array([0.0, driven_length]),
        np.array([0.0, t_shock_end])
    )

    # Path 2: Contact Surface: (0, 0) -> (u2 * t_contact_max, t_contact_max)
    # Contact surface travels until it meets reflected shock or end-wall
    # Reflected shock meets contact surface at (x_coll, t_coll):
    # x_coll = driven_length - w_reflected * (t_coll - t_shock_end) = u2 * t_coll
    # t_coll * (u2 + w_reflected) = driven_length + w_reflected * t_shock_end
    t_coll = (driven_length + w_reflected * t_shock_end) / (u2 + w_reflected)
    x_coll = u2 * t_coll

    wave_paths["Contact Surface"] = (
        np.array([0.0, min(x_coll, driven_length)]),
        np.array([0.0, min(t_coll, t_end)])
    )

    # Path 3: Reflected Shock: (driven_length, t_shock_end) -> (x_coll, t_coll)
    wave_paths["Reflected Shock"] = (
        np.array([driven_length, x_coll]),
        np.array([t_shock_end, t_coll])
    )

    # Path 4: Expansion Fan Head: (0, 0) -> (-driver_length, t_exp_back)
    wave_paths["Expansion Head"] = (
        np.array([0.0, -driver_length]),
        np.array([0.0, t_exp_back])
    )

    # Path 5: Expansion Fan Tail: (0, 0) -> (v_exp_tail * t_tail_end, t_tail_end)
    t_tail_end = min(t_end, abs(driver_length / v_exp_tail) if v_exp_tail < 0 else t_end)
    wave_paths["Expansion Tail"] = (
        np.array([0.0, v_exp_tail * t_tail_end]),
        np.array([0.0, t_tail_end])
    )

    # Path 6: Reflected Expansion Wave (head from driver back wall):
    # (-driver_length, t_exp_back) -> (0, t_emerge_tail) -> (driven_length, t_exp_arr)
    wave_paths["Reflected Expansion"] = (
        np.array([-driver_length, 0.0, test_position]),
        np.array([t_exp_back, t_emerge_tail, t_exp_arr])
    )

    return ShockTubeResult(
        shock_mach=shock_mach,
        driver_gas=driver_gas,
        driven_gas=driven_gas,
        p1=p1,
        t1=t1,
        t4=t4,
        driver_length=driver_length,
        driven_length=driven_length,
        test_position=test_position,
        p4_over_p1=p4_over_p1,
        p4=p4,
        ms_limit=ms_limit,
        a1=a1,
        a4=a4,
        w_shock=w_shock,
        u2=u2,
        w_reflected=w_reflected,
        v_exp_head=v_exp_head,
        v_exp_tail=v_exp_tail,
        rho1=rho1,
        p2=p2,
        t2=t2,
        rho2=rho2,
        a2=a2,
        m2=m2,
        p3=p3,
        t3=t3,
        rho3=rho3,
        a3=a3,
        u3=u3,
        rho4=rho4,
        p5=p5,
        t5=t5,
        rho5=rho5,
        a5=a5,
        mr=mr,
        time_shock_arrival=t_shock_arr,
        time_contact_arrival=t_cs_arr,
        time_expansion_reflect=t_exp_back,
        time_expansion_arrival=t_exp_arr,
        usable_test_window_ms=test_window_ms,
        test_limiting_factor=limiting_factor,
        optimum_driver_length=l4_opt,
        optimum_length_ratio=length_ratio_opt,
        wave_paths=wave_paths
    )
