"""
Gas Dynamics Core Module
------------------------
Implements 1D compressible isentropic flow relations, normal shock wave equations,
gas thermodynamic property lookups, and Sutherland's viscosity model.
Validated against standard NACA 1135 and Anderson Modern Compressible Flow relations.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import math
import numpy as np
from scipy.optimize import brentq


@dataclass(frozen=True)
class GasProperties:
    name: str
    gamma: float           # Specific heat ratio (Cp / Cv)
    R: float               # Specific gas constant (J / (kg * K))
    mol_weight: float      # Molecular weight (g / mol)
    mu_ref: float          # Reference viscosity (Pa * s)
    T_ref: float           # Reference temperature (K)
    S: float               # Sutherland constant (K)


# Standard gases database
GAS_DATABASE: Dict[str, GasProperties] = {
    "Air": GasProperties(
        name="Air",
        gamma=1.400,
        R=287.05,
        mol_weight=28.966,
        mu_ref=1.716e-5,
        T_ref=273.15,
        S=110.4
    ),
    "He": GasProperties(
        name="Helium",
        gamma=1.667,
        R=2077.1,
        mol_weight=4.003,
        mu_ref=1.870e-5,
        T_ref=273.15,
        S=79.4
    ),
    "N2": GasProperties(
        name="Nitrogen",
        gamma=1.400,
        R=296.80,
        mol_weight=28.013,
        mu_ref=1.660e-5,
        T_ref=273.15,
        S=107.0
    ),
    "CO2": GasProperties(
        name="Carbon Dioxide",
        gamma=1.289,
        R=188.92,
        mol_weight=44.010,
        mu_ref=1.370e-5,
        T_ref=273.15,
        S=222.0
    ),
    "Ar": GasProperties(
        name="Argon",
        gamma=1.667,
        R=208.13,
        mol_weight=39.948,
        mu_ref=2.100e-5,
        T_ref=273.15,
        S=144.4
    ),
    "H2": GasProperties(
        name="Hydrogen",
        gamma=1.405,
        R=4124.2,
        mol_weight=2.016,
        mu_ref=0.841e-5,
        T_ref=273.15,
        S=72.0
    )
}


def get_gas(gas_key: str) -> GasProperties:
    """Retrieve gas properties by key (e.g. 'Air', 'He', 'N2'). Case-insensitive."""
    for key, val in GAS_DATABASE.items():
        if key.lower() == gas_key.strip().lower() or val.name.lower() == gas_key.strip().lower():
            return val
    raise ValueError(f"Unknown gas '{gas_key}'. Available: {list(GAS_DATABASE.keys())}")


# ==============================================================================
# 1D Compressible Isentropic Flow Relations
# ==============================================================================

def temp_ratio_isen(M: float, gamma: float = 1.4) -> float:
    """
    Static-to-stagnation temperature ratio: T / T0
    T / T0 = (1 + 0.5 * (gamma - 1) * M^2)^(-1)
    """
    return 1.0 / (1.0 + 0.5 * (gamma - 1.0) * (M ** 2))


def press_ratio_isen(M: float, gamma: float = 1.4) -> float:
    """
    Static-to-stagnation pressure ratio: P / P0
    P / P0 = (1 + 0.5 * (gamma - 1) * M^2)^(-gamma / (gamma - 1))
    """
    t_rat = temp_ratio_isen(M, gamma)
    return t_rat ** (gamma / (gamma - 1.0))


def density_ratio_isen(M: float, gamma: float = 1.4) -> float:
    """
    Static-to-stagnation density ratio: rho / rho0
    rho / rho0 = (1 + 0.5 * (gamma - 1) * M^2)^(-1 / (gamma - 1))
    """
    t_rat = temp_ratio_isen(M, gamma)
    return t_rat ** (1.0 / (gamma - 1.0))


def area_ratio_isen(M: float, gamma: float = 1.4) -> float:
    """
    Cross-sectional area ratio: A / A*
    A / A* = (1 / M) * [ (2 / (gamma + 1)) * (1 + 0.5 * (gamma - 1) * M^2) ]^((gamma + 1) / (2 * (gamma - 1)))
    """
    if M <= 0.0:
        return float('inf')
    if abs(M - 1.0) < 1e-12:
        return 1.0
    factor = (2.0 / (gamma + 1.0)) * (1.0 + 0.5 * (gamma - 1.0) * (M ** 2))
    exponent = (gamma + 1.0) / (2.0 * (gamma - 1.0))
    return (1.0 / M) * (factor ** exponent)


def mach_from_area_ratio(A_over_Astar: float, gamma: float = 1.4, supersonic: bool = True) -> float:
    """
    Invert area-Mach relation: find Mach number for a given A / A*.
    Returns subsonic root if supersonic=False, supersonic root if supersonic=True.
    """
    if A_over_Astar < 1.0 - 1e-9:
        raise ValueError(f"Area ratio A/A* ({A_over_Astar:.4f}) cannot be less than 1.0 for choked flow.")
    if abs(A_over_Astar - 1.0) <= 1e-7:
        return 1.0

    def f(M: float) -> float:
        return area_ratio_isen(M, gamma) - A_over_Astar

    if supersonic:
        # Search range [1.00001, 30.0]
        return brentq(f, 1.000001, 30.0, xtol=1e-8, maxiter=200)
    else:
        # Subsonic range [1e-6, 0.999999]
        return brentq(f, 1e-6, 0.999999, xtol=1e-8, maxiter=200)


def choked_mass_flow_factor(gamma: float = 1.4, R: float = 287.05) -> float:
    """
    Calculates the characteristic choked mass flow parameter:
    C* = sqrt(gamma / R) * (2 / (gamma + 1))^((gamma + 1) / (2 * (gamma - 1)))
    Such that m_dot = C* * P0 * A* / sqrt(T0)
    Units: kg * sqrt(K) / (N * s)
    """
    exp = (gamma + 1.0) / (2.0 * (gamma - 1.0))
    return math.sqrt(gamma / R) * ((2.0 / (gamma + 1.0)) ** exp)


def choked_mass_flow_rate(P0: float, T0: float, A_star: float, gamma: float = 1.4, R: float = 287.05) -> float:
    """
    Calculates mass flow rate through choked throat (kg/s).
    P0 in Pa, T0 in K, A_star in m^2.
    """
    C_star = choked_mass_flow_factor(gamma, R)
    return C_star * (P0 * A_star) / math.sqrt(T0)


def sutherland_viscosity(T: float, gas_key: str = "Air") -> float:
    """
    Dynamic viscosity mu (Pa*s) via Sutherland's law:
    mu = mu_ref * (T / T_ref)^(3/2) * (T_ref + S) / (T + S)
    """
    gas = get_gas(gas_key)
    return gas.mu_ref * ((T / gas.T_ref) ** 1.5) * ((gas.T_ref + gas.S) / (T + gas.S))


# ==============================================================================
# 1D Normal Shock Wave Relations
# ==============================================================================

def normal_shock_mach2(M1: float, gamma: float = 1.4) -> float:
    """
    Downstream Mach number M2 behind a normal shock with upstream Mach M1.
    M2^2 = (2 + (gamma - 1) * M1^2) / (2 * gamma * M1^2 - (gamma - 1))
    """
    if M1 < 1.0:
        return M1
    num = 2.0 + (gamma - 1.0) * (M1 ** 2)
    den = 2.0 * gamma * (M1 ** 2) - (gamma - 1.0)
    return math.sqrt(num / den)


def normal_shock_press_ratio(M1: float, gamma: float = 1.4) -> float:
    """Static pressure ratio across normal shock: P2 / P1."""
    if M1 <= 1.0:
        return 1.0
    return (2.0 * gamma * (M1 ** 2) - (gamma - 1.0)) / (gamma + 1.0)


def normal_shock_temp_ratio(M1: float, gamma: float = 1.4) -> float:
    """Static temperature ratio across normal shock: T2 / T1."""
    if M1 <= 1.0:
        return 1.0
    p_rat = normal_shock_press_ratio(M1, gamma)
    rho_rat = ((gamma + 1.0) * (M1 ** 2)) / (2.0 + (gamma - 1.0) * (M1 ** 2))
    return p_rat / rho_rat


def normal_shock_density_ratio(M1: float, gamma: float = 1.4) -> float:
    """Static density ratio across normal shock: rho2 / rho1."""
    if M1 <= 1.0:
        return 1.0
    return ((gamma + 1.0) * (M1 ** 2)) / (2.0 + (gamma - 1.0) * (M1 ** 2))


def normal_shock_total_press_ratio(M1: float, gamma: float = 1.4) -> float:
    """
    Stagnation pressure ratio across normal shock: P02 / P01
    P02 / P01 = [ (gamma + 1) * M1^2 / ((gamma - 1)*M1^2 + 2) ]^(gamma / (gamma - 1))
                * [ (gamma + 1) / (2*gamma*M1^2 - (gamma - 1)) ]^(1 / (gamma - 1))
    """
    if M1 <= 1.0:
        return 1.0
    t1 = ((gamma + 1.0) * (M1 ** 2)) / ((gamma - 1.0) * (M1 ** 2) + 2.0)
    t2 = (gamma + 1.0) / (2.0 * gamma * (M1 ** 2) - (gamma - 1.0))
    exp1 = gamma / (gamma - 1.0)
    exp2 = 1.0 / (gamma - 1.0)
    return (t1 ** exp1) * (t2 ** exp2)


def rayleigh_pitot_ratio(M1: float, gamma: float = 1.4) -> float:
    """
    Rayleigh Pitot tube formula: P02 / P1 (Total pressure behind shock / static pressure ahead).
    P02 / P1 = [ ((gamma + 1)^2 * M1^2) / (4 * gamma * M1^2 - 2 * (gamma - 1)) ]^(gamma / (gamma - 1))
               * [ (1 - gamma + 2 * gamma * M1^2) / (gamma + 1) ]
    """
    if M1 <= 1.0:
        # Pure isentropic pitot
        return (1.0 + 0.5 * (gamma - 1.0) * (M1 ** 2)) ** (gamma / (gamma - 1.0))
    t1 = (0.5 * (gamma + 1.0) * (M1 ** 2)) ** (gamma / (gamma - 1.0))
    t2 = ((gamma + 1.0) / (2.0 * gamma * (M1 ** 2) - (gamma - 1.0))) ** (1.0 / (gamma - 1.0))
    return t1 * t2
