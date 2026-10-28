"""
Day 4 Batch Generator: Sample Outputs for M = 2.0, 3.0, and 5.0
----------------------------------------------------------------
Generates benchmark aerodynamic solutions, publication-quality figures,
and data tables for the project report.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core import (
    calculate_supersonic_tunnel,
    calculate_shock_tube,
    generate_nozzle_contour,
    theoretical_max_shock_mach
)

# Output directories
OUTPUT_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "outputs")
PLOTS_DIR = os.path.join(OUTPUT_DIR, "plots")
DATA_DIR = os.path.join(OUTPUT_DIR, "data")
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Set high-quality Matplotlib styling
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "lines.linewidth": 2.0,
    "grid.alpha": 0.4,
    "grid.linestyle": "--"
})


def run_benchmark_cases():
    print("=" * 70)
    print("RUNNING BENCHMARK CASES FOR M = 2.0, 3.0, 5.0")
    print("=" * 70)

    mach_cases = [2.0, 3.0, 5.0]

    # Baseline Supersonic Tunnel Parameters
    test_area = 0.04          # 0.2 m x 0.2 m = 0.04 m^2
    tank_pressure_init = 2.0e6 # 2.0 MPa (20 bar)
    tank_volume = 10.0        # 10 m^3
    tank_temp_init = 300.0    # 300 K
    back_pressure = 101325.0  # 1 atm

    # Baseline Hypersonic Shock Tube Parameters
    driver_gas = "He"
    driven_gas = "Air"
    p1 = 10000.0              # 10 kPa
    t1 = 300.0                # 300 K
    t4 = 300.0                # 300 K
    driver_length = 3.0       # 3 m
    driven_length = 9.0       # 9 m

    tunnel_results = []
    shock_results = []
    nozzle_results = []

    for M in mach_cases:
        print(f"\n---> Computing Supersonic Tunnel at Mach {M}...")
        st_res = calculate_supersonic_tunnel(
            mach=M,
            test_area=test_area,
            tank_pressure_init=tank_pressure_init,
            tank_volume=tank_volume,
            tank_temp_init=tank_temp_init,
            back_pressure=back_pressure
        )
        tunnel_results.append(st_res)

        print(f"---> Generating Nozzle Contour for Mach {M}...")
        noz_res = generate_nozzle_contour(mach_design=M, test_area=test_area)
        nozzle_results.append(noz_res)

        print(f"---> Computing Shock Tube for Ms = {M}...")
        sh_res = calculate_shock_tube(
            shock_mach=M,
            driver_gas=driver_gas,
            driven_gas=driven_gas,
            p1=p1,
            t1=t1,
            t4=t4,
            driver_length=driver_length,
            driven_length=driven_length
        )
        shock_results.append(sh_res)

    # --------------------------------------------------------------------------
    # Plot 1: Mach Number vs Nozzle Position x/L (Combined for M=2, 3, 5)
    # --------------------------------------------------------------------------
    fig1, ax1 = plt.subplots(figsize=(10, 6), dpi=300)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for i, (M, noz) in enumerate(zip(mach_cases, nozzle_results)):
        ax1.plot(
            noz.x_normalized,
            noz.mach_distribution,
            color=colors[i],
            label=f"Design $M = {M:.1f}$ (Exit $A/A^* = {area_ratio(M):.2f}$)",
            linewidth=2.5
        )
        # Mark throat position
        idx_throat = np.argmin(np.abs(noz.x_coords))
        ax1.plot(noz.x_normalized[idx_throat], 1.0, "ro", markersize=5)

    ax1.axhline(1.0, color="gray", linestyle=":", alpha=0.7, label="Sonic Throat ($M=1.0$)")
    ax1.set_xlabel("Normalized Nozzle Axial Position, $x / L_{total}$")
    ax1.set_ylabel("Mach Number, $M$")
    ax1.set_title("Supersonic Nozzle Mach Number Distribution ($M(x/L)$)")
    ax1.grid(True)
    ax1.legend(loc="upper left", frameon=True)
    ax1.set_ylim(0.0, 5.5)
    fig1.tight_layout()
    p1_path = os.path.join(PLOTS_DIR, "mach_vs_nozzle_position.png")
    fig1.savefig(p1_path)
    plt.close(fig1)
    print(f"Saved: {p1_path}")

    # --------------------------------------------------------------------------
    # Plot 2: Nozzle Physical Geometry / Contours
    # --------------------------------------------------------------------------
    fig2, ax2 = plt.subplots(figsize=(11, 5.5), dpi=300)
    for i, (M, noz) in enumerate(zip(mach_cases, nozzle_results)):
        ax2.plot(noz.x_coords, noz.y_coords * 100, color=colors[i], label=f"$M = {M:.1f}$ Upper Wall")
        ax2.plot(noz.x_coords, -noz.y_coords * 100, color=colors[i], linestyle="--", alpha=0.6)

    ax2.axvline(0.0, color="black", linestyle=":", alpha=0.8, label="Throat ($x=0$)")
    ax2.set_xlabel("Axial Coordinate $x$ (m)")
    ax2.set_ylabel("Nozzle Half-Height $y$ (cm)")
    ax2.set_title("Supersonic Convergent-Divergent Nozzle Aerodynamic Profiles")
    ax2.grid(True)
    ax2.legend(loc="upper left")
    fig2.tight_layout()
    p2_path = os.path.join(PLOTS_DIR, "nozzle_contours_geometry.png")
    fig2.savefig(p2_path)
    plt.close(fig2)
    print(f"Saved: {p2_path}")

    # --------------------------------------------------------------------------
    # Plot 3: Tank Pressure Decay vs Time during Blow-down
    # --------------------------------------------------------------------------
    fig3, ax3 = plt.subplots(figsize=(10, 6), dpi=300)
    for i, (M, st) in enumerate(zip(mach_cases, tunnel_results)):
        t_arr = st.time_array
        p0_bar = st.p0_time_adiabatic / 1e5
        p0_start_bar = st.p0_starting / 1e5
        p0_run_bar = st.p0_min_running / 1e5

        line, = ax3.plot(t_arr, p0_bar, color=colors[i], label=f"$M = {M:.1f}$ ($t_{{run}} = {st.runtime_adiabatic_to_run:.1f}$ s)")
        # Mark cutoff point
        ax3.plot(st.runtime_adiabatic_to_run, p0_run_bar, marker="s", markersize=6, color=colors[i])
        ax3.axhline(p0_start_bar, color=colors[i], linestyle=":", alpha=0.5)

    ax3.axhline(back_pressure / 1e5, color="red", linestyle="--", label="Atmospheric Pressure (1.01 bar)")
    ax3.set_xlabel("Blow-Down Time, $t$ (seconds)")
    ax3.set_ylabel("Storage Tank Pressure, $P_0(t)$ (bar)")
    ax3.set_title("Storage Tank Pressure Decay vs. Time (Isentropic Blow-Down)")
    ax3.grid(True)
    ax3.legend(loc="upper right", frameon=True)
    ax3.set_xlim(0, max([st.runtime_adiabatic_to_run for st in tunnel_results]) * 1.25)
    fig3.tight_layout()
    p3_path = os.path.join(PLOTS_DIR, "tank_pressure_vs_time.png")
    fig3.savefig(p3_path)
    plt.close(fig3)
    print(f"Saved: {p3_path}")

    # --------------------------------------------------------------------------
    # Plot 4: Shock Tube x-t Wave Diagram (for Ms = 3.0)
    # --------------------------------------------------------------------------
    sh_demo = shock_results[1] # Ms = 3.0
    fig4, ax4 = plt.subplots(figsize=(10, 6.5), dpi=300)

    # Walls
    ax4.axvline(-sh_demo.driver_length, color="black", linewidth=2.5, label="Driver Back Wall ($x=-L_4$)")
    ax4.axvline(0.0, color="gray", linestyle="--", linewidth=1.5, label="Diaphragm ($x=0$)")
    ax4.axvline(sh_demo.driven_length, color="black", linewidth=2.5, label="Driven End Wall ($x=L_1$)")

    # Waves
    wp = sh_demo.wave_paths
    ax4.plot(wp["Incident Shock"][0], wp["Incident Shock"][1] * 1000, "r-", linewidth=2.5, label=f"Incident Shock ($W_s = {sh_demo.w_shock:.0f}$ m/s)")
    ax4.plot(wp["Contact Surface"][0], wp["Contact Surface"][1] * 1000, "b--", linewidth=2.2, label=f"Contact Surface ($u_2 = {sh_demo.u2:.0f}$ m/s)")
    ax4.plot(wp["Reflected Shock"][0], wp["Reflected Shock"][1] * 1000, "m-.", linewidth=2.2, label=f"Reflected Shock ($W_R = {sh_demo.w_reflected:.0f}$ m/s)")
    ax4.plot(wp["Expansion Head"][0], wp["Expansion Head"][1] * 1000, "c-", linewidth=2.0, label="Expansion Head ($-a_4$)")
    ax4.plot(wp["Expansion Tail"][0], wp["Expansion Tail"][1] * 1000, "c:", linewidth=2.0, label="Expansion Tail ($u_3 - a_3$)")
    ax4.plot(wp["Reflected Expansion"][0], wp["Reflected Expansion"][1] * 1000, "g-.", linewidth=1.8, label="Reflected Expansion Head")

    # Shaded Usable Testing Window at End Wall
    t_start_ms = sh_demo.time_shock_arrival * 1000
    t_end_ms = t_start_ms + sh_demo.usable_test_window_ms
    ax4.axvspan(sh_demo.driven_length - 0.2, sh_demo.driven_length, ymin=t_start_ms/25.0, ymax=t_end_ms/25.0, color="gold", alpha=0.5)
    ax4.text(
        sh_demo.driven_length - 0.1, (t_start_ms + t_end_ms) / 2.0,
        f"Test Window\n$\\Delta t = {sh_demo.usable_test_window_ms:.2f}$ ms",
        ha="right", va="center", fontsize=9, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7)
    )

    ax4.set_xlabel("Tube Axial Position $x$ (meters)")
    ax4.set_ylabel("Time $t$ (milliseconds)")
    ax4.set_title(f"Shock Tube Wave Diagram ($x-t$) for $M_s = {sh_demo.shock_mach:.1f}$ ({sh_demo.driver_gas} into {sh_demo.driven_gas})")
    ax4.grid(True)
    ax4.legend(loc="upper left", frameon=True, fontsize=9)
    ax4.set_xlim(-sh_demo.driver_length - 0.5, sh_demo.driven_length + 0.5)
    ax4.set_ylim(0, 25.0)
    fig4.tight_layout()
    p4_path = os.path.join(PLOTS_DIR, "shock_tube_xt_diagram_m3.png")
    fig4.savefig(p4_path)
    plt.close(fig4)
    print(f"Saved: {p4_path}")

    # --------------------------------------------------------------------------
    # Plot 5: Diaphragm Pressure Ratio P4/P1 vs Shock Mach Number
    # --------------------------------------------------------------------------
    fig5, ax5 = plt.subplots(figsize=(9, 6), dpi=300)
    ms_range = np.linspace(1.2, 5.5, 200)

    # He into Air
    p4p1_he = []
    p4p1_n2 = []
    for m_val in ms_range:
        try:
            sh_he = calculate_shock_tube(m_val, "He", "Air", 1e4, 300, 300, 3, 9)
            p4p1_he.append(sh_he.p4_over_p1)
        except ValueError:
            p4p1_he.append(np.nan)

        try:
            sh_n2 = calculate_shock_tube(m_val, "N2", "Air", 1e4, 300, 300, 3, 9)
            p4p1_n2.append(sh_n2.p4_over_p1)
        except ValueError:
            p4p1_n2.append(np.nan)

    ax5.semilogy(ms_range, p4p1_he, "b-", linewidth=2.5, label="Helium Driver into Air ($T_4 = 300$ K)")
    ax5.semilogy(ms_range, p4p1_n2, "r--", linewidth=2.5, label="Nitrogen Driver into Air ($T_4 = 300$ K)")

    # Mark benchmark points
    for sh in shock_results:
        ax5.plot(sh.shock_mach, sh.p4_over_p1, "ko", markersize=6)
        ax5.text(sh.shock_mach + 0.08, sh.p4_over_p1, f"$M_s={sh.shock_mach:.0f}$\n$P_4/P_1={sh.p4_over_p1:.1f}$", fontsize=9)

    ax5.set_xlabel("Target Shock Wave Mach Number, $M_s$")
    ax5.set_ylabel("Required Diaphragm Pressure Ratio, $P_4 / P_1$ (log scale)")
    ax5.set_title("Diaphragm Pressure Ratio vs. Shock Mach Number for Different Driver Gases")
    ax5.grid(True, which="both")
    ax5.legend(loc="upper left", frameon=True)
    fig5.tight_layout()
    p5_path = os.path.join(PLOTS_DIR, "diaphragm_pressure_ratio_vs_ms.png")
    fig5.savefig(p5_path)
    plt.close(fig5)
    print(f"Saved: {p5_path}")

    # --------------------------------------------------------------------------
    # Save Benchmark Data Tables to CSV
    # --------------------------------------------------------------------------
    supersonic_table = []
    for st in tunnel_results:
        supersonic_table.append({
            "Mach": st.mach,
            "Area_Ratio_A_Astar": round(st.area_ratio, 4),
            "Throat_Area_m2": round(st.throat_area, 6),
            "Throat_Diam_cm": round(st.throat_diameter_equiv * 100, 2),
            "Mass_Flow_Init_kg_s": round(st.mass_flow_rate_init, 2),
            "Static_Temp_K": round(st.static_temp, 2),
            "Static_Press_kPa": round(st.static_pressure / 1e3, 2),
            "Velocity_m_s": round(st.flow_velocity, 1),
            "Unit_Re_million_per_m": round(st.unit_reynolds_per_meter / 1e6, 2),
            "P0_Start_bar": round(st.p0_starting / 1e5, 2),
            "P0_Min_Run_bar": round(st.p0_min_running / 1e5, 2),
            "Runtime_Adiabatic_s": round(st.runtime_adiabatic_to_run, 2),
            "Runtime_Isothermal_s": round(st.runtime_isothermal_to_run, 2),
            "Runtime_Regulated_s": round(st.runtime_regulated, 2)
        })

    df_super = pd.DataFrame(supersonic_table)
    csv_super_path = os.path.join(DATA_DIR, "supersonic_tunnel_benchmarks.csv")
    df_super.to_csv(csv_super_path, index=False)
    print(f"Saved: {csv_super_path}")

    shock_table = []
    for sh in shock_results:
        shock_table.append({
            "Shock_Mach_Ms": sh.shock_mach,
            "Driver_Gas": sh.driver_gas,
            "Driven_Gas": sh.driven_gas,
            "P4_over_P1": round(sh.p4_over_p1, 2),
            "Required_P4_bar": round(sh.p4 / 1e5, 2),
            "Shock_Speed_m_s": round(sh.w_shock, 1),
            "Flow_Speed_u2_m_s": round(sh.u2, 1),
            "T2_K": round(sh.t2, 1),
            "P2_kPa": round(sh.p2 / 1e3, 2),
            "T5_Endwall_K": round(sh.t5, 1),
            "P5_Endwall_kPa": round(sh.p5 / 1e3, 2),
            "Test_Window_ms": round(sh.usable_test_window_ms, 2),
            "Limiting_Factor": sh.test_limiting_factor,
            "Optimum_L4_L1_Ratio": round(sh.optimum_length_ratio, 3)
        })

    df_shock = pd.DataFrame(shock_table)
    csv_shock_path = os.path.join(DATA_DIR, "shock_tube_benchmarks.csv")
    df_shock.to_csv(csv_shock_path, index=False)
    print(f"Saved: {csv_shock_path}")

    print("=" * 70)
    print("DAY 4 SAMPLE OUTPUTS AND BENCHMARK RUNS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


def area_ratio(M: float, gamma: float = 1.4) -> float:
    return (1.0 / M) * (((2.0 / (gamma + 1.0)) * (1.0 + 0.5 * (gamma - 1.0) * M ** 2)) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0))))


if __name__ == "__main__":
    run_benchmark_cases()
