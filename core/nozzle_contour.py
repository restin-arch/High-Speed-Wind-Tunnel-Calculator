"""
Supersonic Nozzle Contour and Axial Distribution Module
-------------------------------------------------------
Generates aerodynamic nozzle geometry (convergent-divergent), computes Prandtl-Meyer
expansion limits, and solves 1D isentropic Mach number and flow parameter distributions
M(x/L), P(x/L)/P0, T(x/L)/T0 along the nozzle length.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import math
import numpy as np

from .gas_dynamics import (
    area_ratio_isen,
    mach_from_area_ratio,
    press_ratio_isen,
    temp_ratio_isen,
    get_gas
)


def prandtl_meyer_angle(M: float, gamma: float = 1.4) -> float:
    """
    Computes Prandtl-Meyer angle nu(M) in radians.
    nu(M) = sqrt((gamma+1)/(gamma-1)) * atan(sqrt((gamma-1)/(gamma+1)*(M^2 - 1))) - atan(sqrt(M^2 - 1))
    """
    if M <= 1.0:
        return 0.0
    term1 = math.sqrt((gamma + 1.0) / (gamma - 1.0))
    term2 = math.sqrt(((gamma - 1.0) / (gamma + 1.0)) * (M ** 2 - 1.0))
    term3 = math.sqrt(M ** 2 - 1.0)
    return term1 * math.atan(term2) - math.atan(term3)


@dataclass
class NozzleContourResult:
    mach_design: float
    gamma: float
    throat_radius: float          # y* or r* (m)
    exit_radius: float            # y_e or r_e (m)
    length_convergent: float      # m
    length_divergent: float       # m
    length_total: float           # m
    theta_max_deg: float          # Maximum expansion angle (half PM angle, deg)

    # 1D coordinates
    x_coords: np.ndarray          # Axial position x (m)
    x_normalized: np.ndarray      # x / L_total or x / L_div
    y_coords: np.ndarray          # Upper wall profile y(x) (m)
    area_distribution: np.ndarray # Area A(x) (m^2)
    mach_distribution: np.ndarray # Mach number M(x)
    p_ratio_distribution: np.ndarray # P(x) / P0
    t_ratio_distribution: np.ndarray # T(x) / T0


def generate_nozzle_contour(
    mach_design: float,
    test_area: float,
    gamma: float = 1.4,
    convergent_half_angle_deg: float = 30.0,
    divergent_exit_angle_deg: float = 0.0,
    num_points: int = 300,
    axisymmetric: bool = False
) -> NozzleContourResult:
    """
    Generates a smooth, aerodynamic convergent-divergent supersonic nozzle contour
    and solves the axial flow distribution M(x), P(x)/P0, T(x)/T0.

    Parameters
    ----------
    mach_design : float
        Design exit Mach number (M >= 1.0)
    test_area : float
        Test section exit cross-sectional area (m^2)
    gamma : float, optional
        Specific heat ratio, default 1.4
    convergent_half_angle_deg : float, optional
        Inlet contraction angle (typically 25-45 deg), default 30 deg
    divergent_exit_angle_deg : float, optional
        Nozzle exit wall angle (0 deg for uniform axial flow), default 0 deg
    num_points : int, optional
        Total grid points along nozzle
    axisymmetric : bool, optional
        If True, circular cross-section; if False, 2D planar nozzle

    Returns
    -------
    NozzleContourResult containing wall geometry and aerodynamic profiles.
    """
    if mach_design < 1.0:
        raise ValueError(f"Design Mach number must be >= 1.0 (given {mach_design})")

    A_ratio = area_ratio_isen(mach_design, gamma)
    throat_area = test_area / A_ratio

    if axisymmetric:
        r_exit = math.sqrt(test_area / math.pi)
        r_throat = math.sqrt(throat_area / math.pi)
    else:
        # Planar 2D nozzle with unit width w = 1.0 or square
        # Let's use half-height:
        h_exit = math.sqrt(test_area)
        r_exit = h_exit / 2.0
        # throat half-height
        r_throat = r_exit / A_ratio

    # Maximum expansion angle via Prandtl-Meyer function
    nu_exit = prandtl_meyer_angle(mach_design, gamma)
    theta_max_rad = 0.5 * nu_exit
    theta_max_deg = math.degrees(theta_max_rad)

    # Practical aerodynamic length sizing:
    # Divergent section length: typical fractional length of conical 15-deg nozzle (80% bell)
    # L_div = (r_exit - r_throat) / tan(theta_avg)
    theta_div_avg = math.radians(max(8.0, min(15.0, theta_max_deg)))
    L_div = (r_exit - r_throat) / math.tan(theta_div_avg)

    # Convergent section length: contraction from area ratio ~ 4*A_throat or inlet radius ~ 2*r_throat
    r_inlet = r_throat * 2.0
    L_conv = (r_inlet - r_throat) / math.tan(math.radians(convergent_half_angle_deg))
    L_total = L_conv + L_div

    # Grid generation
    n_conv = int(num_points * (L_conv / L_total))
    n_div = num_points - n_conv

    # Convergent coordinates: x from -L_conv to 0
    # Uses a smooth cubic/cosine contraction
    x_conv = np.linspace(-L_conv, 0.0, n_conv, endpoint=False)
    # Normalized position xi in [0, 1]
    xi_c = (x_conv + L_conv) / L_conv
    # Smooth contraction: r(xi) = r_inlet - (r_inlet - r_throat) * (3*xi^2 - 2*xi^3)
    y_conv = r_inlet - (r_inlet - r_throat) * (3.0 * (xi_c ** 2) - 2.0 * (xi_c ** 3))

    # Divergent coordinates: x from 0 to L_div
    # Uses standard parabolic / 3rd-order polynomial contour:
    # y(0) = r_throat, y'(0) = tan(theta_max), y(L_div) = r_exit, y'(L_div) = tan(divergent_exit_angle)
    x_div = np.linspace(0.0, L_div, n_div)
    s = x_div / L_div  # s in [0, 1]

    tan_theta_0 = math.tan(min(theta_max_rad, math.radians(25.0)))
    tan_theta_e = math.tan(math.radians(divergent_exit_angle_deg))

    # Cubic Hermite spline coefficients for divergent section:
    # y(s) = H00(s)*y0 + H10(s)*L*m0 + H01(s)*y1 + H11(s)*L*m1
    h00 = 2.0 * (s ** 3) - 3.0 * (s ** 2) + 1.0
    h10 = (s ** 3) - 2.0 * (s ** 2) + s
    h01 = -2.0 * (s ** 3) + 3.0 * (s ** 2)
    h11 = (s ** 3) - (s ** 2)

    y_div = (
        h00 * r_throat +
        h10 * (L_div * tan_theta_0) +
        h01 * r_exit +
        h11 * (L_div * tan_theta_e)
    )

    # Combine coordinates
    x_all = np.concatenate([x_conv, x_div])
    y_all = np.concatenate([y_conv, y_div])

    # Compute cross-sectional area along nozzle
    if axisymmetric:
        area_all = math.pi * (y_all ** 2)
    else:
        # width * (2 * y)
        w = math.sqrt(test_area)
        area_all = w * (2.0 * y_all)

    # Area ratio A(x) / A*
    A_over_Astar_all = area_all / throat_area
    A_over_Astar_all = np.maximum(A_over_Astar_all, 1.0)

    # Solve Mach number M(x) along nozzle
    mach_all = np.zeros_like(x_all)
    for i, (x_val, ar) in enumerate(zip(x_all, A_over_Astar_all)):
        if x_val < 0.0:
            # Subsonic branch
            mach_all[i] = mach_from_area_ratio(ar, gamma=gamma, supersonic=False)
        elif abs(x_val) < 1e-9:
            mach_all[i] = 1.0
        else:
            # Supersonic branch
            mach_all[i] = mach_from_area_ratio(ar, gamma=gamma, supersonic=True)

    # Pressure and Temperature distributions
    p_ratio_all = np.array([press_ratio_isen(m, gamma) for m in mach_all])
    t_ratio_all = np.array([temp_ratio_isen(m, gamma) for m in mach_all])

    # Normalized x coordinate x / L_total (offset so 0 is at inlet or 0 at throat)
    x_norm = (x_all + L_conv) / L_total

    return NozzleContourResult(
        mach_design=mach_design,
        gamma=gamma,
        throat_radius=r_throat,
        exit_radius=r_exit,
        length_convergent=L_conv,
        length_divergent=L_div,
        length_total=L_total,
        theta_max_deg=theta_max_deg,
        x_coords=x_all,
        x_normalized=x_norm,
        y_coords=y_all,
        area_distribution=area_all,
        mach_distribution=mach_all,
        p_ratio_distribution=p_ratio_all,
        t_ratio_distribution=t_ratio_all
    )
