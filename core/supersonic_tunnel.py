"""
Supersonic Blow-Down Wind Tunnel Module
---------------------------------------
Handles aerodynamic design, throat sizing, test-section flow properties,
starting/running pressure limits, and unsteady tank blow-down decay and runtime estimation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import numpy as np

from .gas_dynamics import (
    get_gas,
    temp_ratio_isen,
    press_ratio_isen,
    density_ratio_isen,
    area_ratio_isen,
    choked_mass_flow_factor,
    choked_mass_flow_rate,
    normal_shock_total_press_ratio,
    normal_shock_press_ratio,
    sutherland_viscosity
)


@dataclass
class SupersonicDesignResult:
    # Inputs echoed
    mach: float
    test_area: float              # m^2
    tank_pressure_init: float     # Pa
    tank_volume: float            # m^3
    tank_temp_init: float         # K
    back_pressure: float          # Pa
    gas_name: str

    # Geometric sizing
    area_ratio: float             # A / A*
    throat_area: float            # m^2
    test_diameter_equiv: float    # m (equivalent circular)
    throat_diameter_equiv: float  # m (equivalent circular)

    # Initial flow state at test section
    static_temp: float            # K
    static_pressure: float        # Pa
    static_density: float         # kg / m^3
    flow_velocity: float          # m / s
    dynamic_pressure: float       # Pa
    speed_of_sound: float         # m / s
    mass_flow_rate_init: float    # kg / s
    unit_reynolds_per_meter: float# 1 / m
    viscosity: float              # Pa * s

    # Tunnel pressure limits
    normal_shock_p0_ratio: float  # P02 / P01 at test Mach
    p0_min_running: float         # Minimum P0 to maintain supersonic flow (Pa)
    p0_starting: float            # Minimum P0 required to swallow starting shock (Pa)

    # Runtimes
    runtime_adiabatic_to_start: float # s (time until P0 drops to P0_start)
    runtime_adiabatic_to_run: float   # s (time until P0 drops to P0_min_running)
    runtime_isothermal_to_run: float  # s (under constant T0 assumption)
    runtime_regulated: float          # s (with pressure reducer regulating to P0_start)

    # Time history arrays for plotting
    time_array: np.ndarray = field(default_factory=lambda: np.array([]))
    p0_time_adiabatic: np.ndarray = field(default_factory=lambda: np.array([]))
    t0_time_adiabatic: np.ndarray = field(default_factory=lambda: np.array([]))
    mdot_time_adiabatic: np.ndarray = field(default_factory=lambda: np.array([]))
    p0_time_isothermal: np.ndarray = field(default_factory=lambda: np.array([]))


def calculate_supersonic_tunnel(
    mach: float,
    test_area: float,
    tank_pressure_init: float,
    tank_volume: float,
    tank_temp_init: float = 300.0,
    back_pressure: float = 101325.0,
    gas_name: str = "Air",
    start_safety_factor: float = 1.25,
    diffuser_efficiency: float = 0.85,
    num_time_points: int = 500
) -> SupersonicDesignResult:
    """
    Complete aerodynamic sizing and runtime analysis for a supersonic blow-down wind tunnel.

    Parameters
    ----------
    mach : float
        Design test-section Mach number (M >= 1.0)
    test_area : float
        Test section cross-sectional area (m^2)
    tank_pressure_init : float
        Initial storage tank pressure (Pa)
    tank_volume : float
        Storage tank volume (m^3)
    tank_temp_init : float, optional
        Initial storage tank stagnation temperature (K), default 300 K
    back_pressure : float, optional
        Atmospheric or exhaust back pressure (Pa), default 101325 Pa
    gas_name : str, optional
        Working gas name (e.g. 'Air', 'N2', 'He'), default 'Air'
    start_safety_factor : float, optional
        Starting pressure margin factor (typically 1.15 to 1.35), default 1.25
    diffuser_efficiency : float, optional
        Diffuser pressure recovery efficiency, default 0.85
    num_time_points : int, optional
        Number of steps for plotting arrays

    Returns
    -------
    SupersonicDesignResult dataclass containing full sizing and time histories.
    """
    if mach < 1.0:
        raise ValueError(f"Supersonic wind tunnel Mach number must be >= 1.0 (given {mach})")
    if test_area <= 0.0 or tank_volume <= 0.0 or tank_pressure_init <= 0.0:
        raise ValueError("Dimensions, volume, and pressures must be strictly positive.")

    gas = get_gas(gas_name)
    gamma = gas.gamma
    R = gas.R

    # 1. Throat sizing via Area-Mach relation
    A_over_Astar = area_ratio_isen(mach, gamma)
    throat_area = test_area / A_over_Astar
    test_diam = math.sqrt(4.0 * test_area / math.pi)
    throat_diam = math.sqrt(4.0 * throat_area / math.pi)

    # 2. Initial test section flow conditions
    T_ratio = temp_ratio_isen(mach, gamma)
    P_ratio = press_ratio_isen(mach, gamma)

    T_static = tank_temp_init * T_ratio
    P_static = tank_pressure_init * P_ratio
    rho_static = P_static / (R * T_static)
    a_sound = math.sqrt(gamma * R * T_static)
    velocity = mach * a_sound
    q_dyn = 0.5 * rho_static * (velocity ** 2)

    # Sutherland dynamic viscosity & unit Reynolds number
    mu = sutherland_viscosity(T_static, gas_name)
    unit_Re = (rho_static * velocity) / mu if mu > 0 else 0.0

    # Choked mass flow rate at throat at t=0
    mdot_init = choked_mass_flow_rate(tank_pressure_init, tank_temp_init, throat_area, gamma, R)
    initial_gas_mass = (tank_pressure_init * tank_volume) / (R * tank_temp_init)

    # 3. Tunnel Operating & Starting Pressure Requirements (Liepmann & Roshko / Anderson)
    # Total pressure ratio across normal shock at test Mach: P02 / P01
    p02_over_p01 = normal_shock_total_press_ratio(mach, gamma)

    # Minimum theoretical running pressure:
    # A normal shock standing in the diffuser or test section
    # P0_min_running = P_back / (P02 / P01 * diffuser_efficiency + (1 - diffuser_efficiency)*P_static/P0)
    p0_min_run = back_pressure / max(p02_over_p01 * diffuser_efficiency, 1e-4)

    # Starting pressure:
    # Requires swallowing the shock through the test section:
    # P0_start = P_back / (P02 / P01) * start_safety_factor
    p0_start = (back_pressure / p02_over_p01) * start_safety_factor

    # Ensure p0_start >= p0_min_run
    p0_start = max(p0_start, p0_min_run * 1.1)

    # Check if tank pressure is sufficient to start the tunnel
    can_start = tank_pressure_init >= p0_start

    # 4. Blow-down pressure decay & runtime calculations
    # Characteristic discharge rate constant tau (1 / s):
    # tau = (A* * sqrt(gamma * R * T0_init) / V) * (2 / (gamma + 1))^((gamma + 1) / (2*(gamma - 1)))
    C_star = choked_mass_flow_factor(gamma, R)
    tau = (C_star * throat_area * math.sqrt(tank_temp_init) * R) / tank_volume

    # Analytical runtime for adiabatic discharge:
    # P0(t) = P0_init * [ 1 + ((gamma - 1) / 2) * tau * t ]^(-2 * gamma / (gamma - 1))
    def calc_adiabatic_t(target_p0: float) -> float:
        if tank_pressure_init <= target_p0:
            return 0.0
        exponent = (gamma - 1.0) / (2.0 * gamma)
        pressure_factor = (tank_pressure_init / target_p0) ** exponent
        return (2.0 / ((gamma - 1.0) * tau)) * (pressure_factor - 1.0)

    # Analytical runtime for isothermal discharge:
    # P0(t) = P0_init * exp(-tau * t)
    def calc_isothermal_t(target_p0: float) -> float:
        if tank_pressure_init <= target_p0:
            return 0.0
        return (1.0 / tau) * math.log(tank_pressure_init / target_p0)

    t_adia_to_start = calc_adiabatic_t(p0_start)
    t_adia_to_run = calc_adiabatic_t(p0_min_run)
    t_iso_to_run = calc_isothermal_t(p0_min_run)

    # Regulated blow-down runtime:
    # Stagnation pressure in settling chamber is held constant at P0_start
    # Flow rate is constant: mdot_reg = mdot(P0_start, T0_init)
    # Gas in tank expands until tank pressure reaches P0_start
    if tank_pressure_init > p0_start:
        mdot_reg = choked_mass_flow_rate(p0_start, tank_temp_init, throat_area, gamma, R)
        # Assuming isentropic expansion of remaining tank contents:
        # T_final = T0_init * (p0_start / tank_pressure_init)^((gamma - 1)/gamma)
        T_tank_final = tank_temp_init * ((p0_start / tank_pressure_init) ** ((gamma - 1.0) / gamma))
        final_gas_mass = (p0_start * tank_volume) / (R * T_tank_final)
        usable_mass = max(0.0, initial_gas_mass - final_gas_mass)
        t_regulated = usable_mass / mdot_reg if mdot_reg > 0 else 0.0
    else:
        t_regulated = 0.0

    # 5. Generate time history arrays for plots
    t_max = max(t_adia_to_run * 1.3, 5.0)
    time_arr = np.linspace(0.0, t_max, num_time_points)

    # Adiabatic decay
    factor_arr = 1.0 + 0.5 * (gamma - 1.0) * tau * time_arr
    p0_adia_arr = tank_pressure_init * (factor_arr ** (-2.0 * gamma / (gamma - 1.0)))
    t0_adia_arr = tank_temp_init * (factor_arr ** -2.0)
    mdot_adia_arr = mdot_init * (factor_arr ** (-(gamma + 1.0) / (gamma - 1.0)))

    # Isothermal decay
    p0_iso_arr = tank_pressure_init * np.exp(-tau * time_arr)

    return SupersonicDesignResult(
        mach=mach,
        test_area=test_area,
        tank_pressure_init=tank_pressure_init,
        tank_volume=tank_volume,
        tank_temp_init=tank_temp_init,
        back_pressure=back_pressure,
        gas_name=gas_name,
        area_ratio=A_over_Astar,
        throat_area=throat_area,
        test_diameter_equiv=test_diam,
        throat_diameter_equiv=throat_diam,
        static_temp=T_static,
        static_pressure=P_static,
        static_density=rho_static,
        flow_velocity=velocity,
        dynamic_pressure=q_dyn,
        speed_of_sound=a_sound,
        mass_flow_rate_init=mdot_init,
        unit_reynolds_per_meter=unit_Re,
        viscosity=mu,
        normal_shock_p0_ratio=p02_over_p01,
        p0_min_running=p0_min_run,
        p0_starting=p0_start,
        runtime_adiabatic_to_start=t_adia_to_start,
        runtime_adiabatic_to_run=t_adia_to_run,
        runtime_isothermal_to_run=t_iso_to_run,
        runtime_regulated=t_regulated,
        time_array=time_arr,
        p0_time_adiabatic=p0_adia_arr,
        t0_time_adiabatic=t0_adia_arr,
        mdot_time_adiabatic=mdot_adia_arr,
        p0_time_isothermal=p0_iso_arr
    )
