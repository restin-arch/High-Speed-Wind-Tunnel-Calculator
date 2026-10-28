"""
Supersonic and Hypersonic Wind Tunnel Design Package.
"""
from .gas_dynamics import (
    GAS_DATABASE,
    GasProperties,
    get_gas,
    temp_ratio_isen,
    press_ratio_isen,
    density_ratio_isen,
    area_ratio_isen,
    mach_from_area_ratio,
    choked_mass_flow_factor,
    choked_mass_flow_rate,
    sutherland_viscosity,
    normal_shock_mach2,
    normal_shock_press_ratio,
    normal_shock_temp_ratio,
    normal_shock_density_ratio,
    normal_shock_total_press_ratio,
    rayleigh_pitot_ratio
)

from .supersonic_tunnel import (
    SupersonicDesignResult,
    calculate_supersonic_tunnel
)

from .shock_tube import (
    ShockTubeResult,
    calculate_shock_tube,
    theoretical_max_shock_mach
)

from .nozzle_contour import (
    NozzleContourResult,
    generate_nozzle_contour,
    prandtl_meyer_angle
)
