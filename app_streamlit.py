"""
Streamlit Web Application
=========================
Supersonic & Hypersonic Wind Tunnel Design & Runtime Calculator
Modules:
  - Module 2: Supersonic Blow-Down Wind Tunnel (Nozzle sizing, flow states, tank decay, runtime)
  - Module 3: Hypersonic Shock Tube (P4/P1 ratio, states 1-5, x-t wave diagram, usable testing window)
"""

import os
import sys
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core import (
    calculate_supersonic_tunnel,
    calculate_shock_tube,
    generate_nozzle_contour,
    GAS_DATABASE,
    area_ratio_isen
)

# Page configuration
st.set_page_config(
    page_title="High-Speed Wind Tunnel Calculator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished aerospace look
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 12px 16px;
        border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.05rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.markdown('<div class="main-header">🚀 High-Speed Wind Tunnel & Shock Tube Calculator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Automated Nozzle Sizing, Blow-Down Runtime & Hypersonic Shock Wave Dynamics (Modules 2 & 3)</div>', unsafe_allow_html=True)

    # Sidebar controls
    st.sidebar.image("https://img.icons8.com/fluency/96/wind-turbine.png", width=64)
    st.sidebar.title("Configuration")

    module_choice = st.sidebar.radio(
        "Select Module:",
        [
            "Module 2: Supersonic Blow-Down Tunnel",
            "Module 3: Hypersonic Shock Tube",
            "Benchmark Comparison (M = 2, 3, 5)"
        ]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **Aerospace Gas Dynamics Toolkit**
    - 1D Compressible Isentropic Flow
    - Normal Shock Wave Relations
    - Unsteady Reservoir Blow-Down Decay
    - 1D Riemann Shock Tube Dynamics
    """)

    if module_choice == "Module 2: Supersonic Blow-Down Tunnel":
        render_supersonic_module()
    elif module_choice == "Module 3: Hypersonic Shock Tube":
        render_shock_tube_module()
    else:
        render_benchmarks_module()


# ==============================================================================
# MODULE 2: SUPERSONIC BLOW-DOWN WIND TUNNEL
# ==============================================================================
def render_supersonic_module():
    st.subheader("💨 Module 2: Supersonic Blow-Down Wind Tunnel")
    st.caption("Calculates choked nozzle throat sizing, 1D flow states, starting/running pressure thresholds, and storage tank pressure decay runtime.")

    col_in, col_view = st.columns([1, 2], gap="large")

    with col_in:
        st.markdown("### 📥 Tunnel Design Inputs")

        mach = st.slider("Desired Test Section Mach Number (M)", min_value=1.1, max_value=6.0, value=2.5, step=0.1)

        input_mode = st.radio("Test Section Geometry Input:", ["Area (m²)", "Dimensions (Width × Height cm)"], horizontal=True)
        if input_mode == "Area (m²)":
            test_area = st.number_input("Test Section Area A (m²)", min_value=0.001, max_value=2.0, value=0.04, step=0.005, format="%.4f")
        else:
            w_cm = st.number_input("Width (cm)", min_value=2.0, max_value=200.0, value=20.0, step=1.0)
            h_cm = st.number_input("Height (cm)", min_value=2.0, max_value=200.0, value=20.0, step=1.0)
            test_area = (w_cm / 100.0) * (h_cm / 100.0)
            st.info(f"Cross-sectional area: {test_area * 1e4:.1f} cm² ({test_area:.4f} m²)")

        p0_bar = st.number_input("Storage Tank Initial Stagnation Pressure P₀ (bar)", min_value=1.5, max_value=200.0, value=20.0, step=1.0)
        v_tank = st.number_input("Storage Tank Volume V (m³)", min_value=0.1, max_value=500.0, value=10.0, step=0.5)
        t0_init = st.number_input("Storage Tank Initial Temperature T₀ (K)", min_value=100.0, max_value=800.0, value=300.0, step=10.0)
        p_back_bar = st.number_input("Exhaust / Ambient Back Pressure (bar)", min_value=0.01, max_value=5.0, value=1.01325, step=0.05)

        gas_name = st.selectbox("Working Gas", list(GAS_DATABASE.keys()), index=0)

        with st.expander("Advanced Aerodynamic Tuning"):
            safety_factor = st.slider("Starting Pressure Safety Margin", min_value=1.05, max_value=1.50, value=1.25, step=0.05)
            diff_eff = st.slider("Diffuser Pressure Recovery Efficiency", min_value=0.50, max_value=0.98, value=0.85, step=0.05)

    # Perform calculations
    res = calculate_supersonic_tunnel(
        mach=mach,
        test_area=test_area,
        tank_pressure_init=p0_bar * 1e5,
        tank_volume=v_tank,
        tank_temp_init=t0_init,
        back_pressure=p_back_bar * 1e5,
        gas_name=gas_name,
        start_safety_factor=safety_factor,
        diffuser_efficiency=diff_eff
    )
    noz = generate_nozzle_contour(mach_design=mach, test_area=test_area)

    with col_view:
        st.markdown("### 📊 Key Performance Metrics")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Area Ratio (A/A*)", f"{res.area_ratio:.3f}")
        kpi1.metric("Throat Area (A*)", f"{res.throat_area * 1e4:.2f} cm²")

        kpi2.metric("Initial Mass Flow (ṁ)", f"{res.mass_flow_rate_init:.1f} kg/s")
        kpi2.metric("Flow Velocity (u)", f"{res.flow_velocity:.0f} m/s")

        kpi3.metric("P₀ Starting Req.", f"{res.p0_starting / 1e5:.2f} bar")
        kpi3.metric("P₀ Min. Running", f"{res.p0_min_running / 1e5:.2f} bar")

        kpi4.metric("Runtime (Adiabatic)", f"{res.runtime_adiabatic_to_run:.2f} s")
        kpi4.metric("Runtime (Regulated)", f"{res.runtime_regulated:.2f} s")

        if p0_bar < (res.p0_starting / 1e5):
            st.warning(f"⚠️ Initial tank pressure ({p0_bar:.1f} bar) is lower than the starting pressure ({res.p0_starting/1e5:.2f} bar) required to swallow the normal shock!")

        # Plots Tabs
        tab_p1, tab_p2, tab_p3 = st.tabs(["📈 Mach Distribution M(x/L)", "⏱️ Tank Pressure Decay P₀(t)", "📐 Nozzle Profile Geometry"])

        with tab_p1:
            fig, ax = plt.subplots(figsize=(8, 4.2), dpi=200)
            ax.plot(noz.x_normalized, noz.mach_distribution, color="#2563eb", linewidth=2.5, label="Flow Mach $M(x/L)$")
            idx_th = np.argmin(np.abs(noz.x_coords))
            ax.plot(noz.x_normalized[idx_th], 1.0, "ro", markersize=6, label="Sonic Throat ($M=1.0$)")
            ax.axhline(1.0, color="gray", linestyle=":", alpha=0.6)
            ax.set_xlabel("Normalized Nozzle Axial Position, $x / L_{total}$")
            ax.set_ylabel("Mach Number, $M$")
            ax.set_title(f"Mach Number vs. Axial Position for Design Exit $M = {mach:.2f}$")
            ax.grid(True, alpha=0.4)
            ax.legend(loc="upper left")
            st.pyplot(fig)
            plt.close(fig)

        with tab_p2:
            fig, ax = plt.subplots(figsize=(8, 4.2), dpi=200)
            ax.plot(res.time_array, res.p0_time_adiabatic / 1e5, color="#dc2626", linewidth=2.5, label="Adiabatic Tank $P_0(t)$")
            ax.plot(res.time_array, res.p0_time_isothermal / 1e5, color="#16a34a", linestyle="--", linewidth=1.8, label="Isothermal Tank $P_0(t)$")
            ax.axhline(res.p0_starting / 1e5, color="#d97706", linestyle=":", label=f"Starting Limit = {res.p0_starting/1e5:.2f} bar")
            ax.axhline(res.p0_min_running / 1e5, color="#9333ea", linestyle=":", label=f"Unchoke Limit = {res.p0_min_running/1e5:.2f} bar")
            if res.runtime_adiabatic_to_run > 0:
                ax.plot(res.runtime_adiabatic_to_run, res.p0_min_running / 1e5, "ks", markersize=7, label=f"Cutoff $t_{{run}} = {res.runtime_adiabatic_to_run:.1f}$ s")
            ax.set_xlabel("Time, $t$ (seconds)")
            ax.set_ylabel("Storage Tank Pressure, $P_0$ (bar)")
            ax.set_title("Tank Pressure Decay vs. Time during Blow-Down")
            ax.grid(True, alpha=0.4)
            ax.legend(loc="upper right", fontsize=8)
            st.pyplot(fig)
            plt.close(fig)

        with tab_p3:
            fig, ax = plt.subplots(figsize=(8, 3.8), dpi=200)
            ax.plot(noz.x_coords, noz.y_coords * 100, color="#1e3a8a", linewidth=2.2, label="Upper Nozzle Wall")
            ax.plot(noz.x_coords, -noz.y_coords * 100, color="#1e3a8a", linewidth=2.2, linestyle="--", alpha=0.7, label="Lower Wall")
            ax.axvline(0.0, color="red", linestyle=":", label="Throat ($x=0$)")
            ax.set_xlabel("Axial Distance, $x$ (m)")
            ax.set_ylabel("Half-Height, $y$ (cm)")
            ax.set_title(f"Aerodynamic Convergent-Divergent Nozzle Contour (Divergent Length = {noz.length_divergent:.2f} m)")
            ax.grid(True, alpha=0.4)
            ax.legend(loc="upper left")
            st.pyplot(fig)
            plt.close(fig)

    st.markdown("---")
    st.markdown("### 📋 Test Section Aerodynamic State Properties (at $t=0$)")
    df_state = pd.DataFrame({
        "Property": [
            "Test Mach Number",
            "Cross-Sectional Area",
            "Throat Area (A*)",
            "Equiv. Throat Diameter",
            "Static Pressure",
            "Static Temperature",
            "Static Density",
            "Flow Velocity",
            "Dynamic Pressure",
            "Dynamic Viscosity",
            "Unit Reynolds Number",
            "Initial Mass Flow Rate"
        ],
        "Value": [
            f"{res.mach:.2f}",
            f"{res.test_area * 1e4:.2f} cm² ({res.test_area:.4f} m²)",
            f"{res.throat_area * 1e4:.2f} cm² ({res.throat_area:.6f} m²)",
            f"{res.throat_diameter_equiv * 100:.2f} cm",
            f"{res.static_pressure / 1e3:.2f} kPa ({res.static_pressure / 1e5:.3f} bar)",
            f"{res.static_temp:.1f} K ({res.static_temp - 273.15:.1f} °C)",
            f"{res.static_density:.4f} kg/m³",
            f"{res.flow_velocity:.1f} m/s",
            f"{res.dynamic_pressure / 1e3:.2f} kPa",
            f"{res.viscosity * 1e6:.2f} µPa·s",
            f"{res.unit_reynolds_per_meter / 1e6:.2f} × 10⁶ /m",
            f"{res.mass_flow_rate_init:.2f} kg/s"
        ]
    })
    st.table(df_state)


# ==============================================================================
# MODULE 3: HYPERSONIC SHOCK TUBE
# ==============================================================================
def render_shock_tube_module():
    st.subheader("⚡ Module 3: Hypersonic Shock Tube / Runtime Calculator")
    st.caption("Solves the fundamental 1D shock tube relation, intermediate states 1-5, wave kinematics, and usable testing window duration.")

    col_in, col_view = st.columns([1, 2], gap="large")

    with col_in:
        st.markdown("### 📥 Shock Tube Inputs")
        target_ms = st.slider("Target Shock Wave Mach Number (Mₛ)", min_value=1.2, max_value=7.0, value=3.0, step=0.1)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            driver_gas = st.selectbox("Driver Gas", ["He", "N2", "H2", "Air"], index=0)
        with col_g2:
            driven_gas = st.selectbox("Driven Gas", ["Air", "N2", "CO2", "Ar"], index=0)

        p1_kpa = st.number_input("Driven Gas Initial Pressure P₁ (kPa)", min_value=0.1, max_value=500.0, value=10.0, step=1.0)
        t1_k = st.number_input("Driven Gas Temperature T₁ (K)", min_value=100.0, max_value=500.0, value=300.0, step=10.0)
        t4_k = st.number_input("Driver Gas Temperature T₄ (K)", min_value=100.0, max_value=2000.0, value=300.0, step=25.0)

        st.markdown("##### Tube Geometry")
        driver_len = st.number_input("Driver Section Length L₄ (m)", min_value=0.2, max_value=30.0, value=3.0, step=0.5)
        driven_len = st.number_input("Driven Section Length L₁ (m)", min_value=0.5, max_value=50.0, value=9.0, step=0.5)
        test_pos = st.number_input("Test Station Position x_ts (m from diaphragm)", min_value=0.1, max_value=float(driven_len), value=float(driven_len), step=0.5)

    try:
        sh = calculate_shock_tube(
            shock_mach=target_ms,
            driver_gas=driver_gas,
            driven_gas=driven_gas,
            p1=p1_kpa * 1e3,
            t1=t1_k,
            t4=t4_k,
            driver_length=driver_len,
            driven_length=driven_len,
            test_position=test_pos
        )
    except Exception as e:
        st.error(f"Computation error: {str(e)}")
        return

    with col_view:
        st.markdown("### 📊 Shock Dynamics & Runtime Metrics")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Pressure Ratio (P₄/P₁)", f"{sh.p4_over_p1:.2f}")
        k1.metric("Driver Pressure (P₄)", f"{sh.p4 / 1e5:.2f} bar")

        k2.metric("Incident Shock (Wₛ)", f"{sh.w_shock:.0f} m/s")
        k2.metric("Induced Flow (u₂)", f"{sh.u2:.0f} m/s")

        k3.metric("Post-Shock Temp (T₂)", f"{sh.t2:.0f} K")
        k3.metric("Reflected Temp (T₅)", f"{sh.t5:.0f} K")

        k4.metric("Usable Test Window", f"{sh.usable_test_window_ms:.2f} ms")
        k4.metric("Optimum L₄/L₁ Ratio", f"{sh.optimum_length_ratio:.3f}")

        st.info(f"⏱️ **Testing Window Limit:** Terminated by **{sh.test_limiting_factor}** at {test_pos:.1f} m from diaphragm.")

        tab_xt, tab_sens = st.tabs(["📈 Shock Tube Wave Diagram (x-t)", "📉 Pressure Ratio Sensitivity (P₄/P₁ vs Mₛ)"])

        with tab_xt:
            fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=200)
            wp = sh.wave_paths
            ax.axvline(-sh.driver_length, color="black", linewidth=2.2, label="Driver Wall ($x=-L_4$)")
            ax.axvline(0.0, color="gray", linestyle="--", linewidth=1.2, label="Diaphragm ($x=0$)")
            ax.axvline(sh.driven_length, color="black", linewidth=2.2, label="Driven Wall ($x=L_1$)")

            ax.plot(wp["Incident Shock"][0], wp["Incident Shock"][1] * 1000, "r-", linewidth=2.2, label="Incident Shock")
            ax.plot(wp["Contact Surface"][0], wp["Contact Surface"][1] * 1000, "b--", linewidth=1.8, label="Contact Surface")
            ax.plot(wp["Reflected Shock"][0], wp["Reflected Shock"][1] * 1000, "m-.", linewidth=1.8, label="Reflected Shock")
            ax.plot(wp["Expansion Head"][0], wp["Expansion Head"][1] * 1000, "c-", linewidth=1.5, label="Expansion Head")
            ax.plot(wp["Expansion Tail"][0], wp["Expansion Tail"][1] * 1000, "c:", linewidth=1.5, label="Expansion Tail")
            ax.plot(wp["Reflected Expansion"][0], wp["Reflected Expansion"][1] * 1000, "g-.", linewidth=1.5, label="Refl. Expansion")

            t_start_ms = sh.time_shock_arrival * 1000
            t_win = sh.usable_test_window_ms
            ax.axvspan(test_pos - 0.25, test_pos, ymin=t_start_ms/30.0, ymax=(t_start_ms+t_win)/30.0, color="gold", alpha=0.6)
            ax.text(test_pos - 0.1, t_start_ms + t_win/2, f"Δt={t_win:.2f} ms", ha="right", va="center", fontsize=8, fontweight="bold")

            ax.set_xlabel("Tube Position, $x$ (meters)")
            ax.set_ylabel("Time, $t$ (milliseconds)")
            ax.set_title(f"Wave Diagram ($x-t$) for $M_s = {sh.shock_mach:.1f}$ ({sh.driver_gas} into {sh.driven_gas})")
            ax.grid(True, alpha=0.4)
            ax.legend(loc="upper left", fontsize=8)
            ax.set_ylim(0, max(25.0, (t_start_ms + t_win) * 1.5))
            st.pyplot(fig)
            plt.close(fig)

        with tab_sens:
            fig, ax = plt.subplots(figsize=(8.5, 4.4), dpi=200)
            ms_arr = np.linspace(1.2, min(6.0, sh.ms_limit - 0.05), 100)
            p4p1_curr = []
            for m in ms_arr:
                try:
                    s_t = calculate_shock_tube(m, driver_gas, driven_gas, p1_kpa * 1e3, t1_k, t4_k, driver_len, driven_len)
                    p4p1_curr.append(s_t.p4_over_p1)
                except Exception:
                    p4p1_curr.append(np.nan)

            ax.semilogy(ms_arr, p4p1_curr, color="#2563eb", linewidth=2.2, label=f"{driver_gas} into {driven_gas}")
            ax.plot(sh.shock_mach, sh.p4_over_p1, "ro", markersize=7, label=f"Current $M_s={sh.shock_mach:.1f}$ ($P_4/P_1={sh.p4_over_p1:.1f}$)")
            ax.set_xlabel("Shock Mach Number $M_s$")
            ax.set_ylabel("Diaphragm Pressure Ratio $P_4 / P_1$")
            ax.set_title("Required Diaphragm Pressure Ratio vs. Shock Mach Number")
            ax.grid(True, which="both", alpha=0.4)
            ax.legend(loc="upper left")
            st.pyplot(fig)
            plt.close(fig)

    st.markdown("---")
    st.markdown("### 📋 Complete State Summary Table (States 1 to 5)")
    df_sh_states = pd.DataFrame({
        "State": ["State 1 (Quiescent Driven)", "State 2 (Behind Incident Shock)", "State 3 (Expanded Driver)", "State 4 (Quiescent Driver)", "State 5 (Reflected Reservoir)"],
        "Gas": [sh.driven_gas, sh.driven_gas, sh.driver_gas, sh.driver_gas, sh.driven_gas],
        "Pressure (kPa)": [f"{sh.p1/1e3:.2f}", f"{sh.p2/1e3:.2f}", f"{sh.p3/1e3:.2f}", f"{sh.p4/1e3:.2f}", f"{sh.p5/1e3:.2f}"],
        "Temperature (K)": [f"{sh.t1:.1f}", f"{sh.t2:.1f}", f"{sh.t3:.1f}", f"{sh.t4:.1f}", f"{sh.t5:.1f}"],
        "Density (kg/m³)": [f"{sh.rho1:.4f}", f"{sh.rho2:.4f}", f"{sh.rho3:.4f}", f"{sh.rho4:.4f}", f"{sh.rho5:.4f}"],
        "Velocity (m/s)": ["0.0", f"{sh.u2:.1f}", f"{sh.u3:.1f}", "0.0", "0.0"]
    })
    st.table(df_sh_states)


# ==============================================================================
# BENCHMARK COMPARISONS (M = 2, 3, 5)
# ==============================================================================
def render_benchmarks_module():
    st.subheader("📚 Day 4: Benchmark Aerodynamic Comparisons for M = 2.0, 3.0, 5.0")
    st.caption("Standard validation benchmark cases covering supersonic nozzle throat sizing, blow-down decay, and hypersonic shock tube requirements.")

    # Load pre-generated benchmark CSVs if present, else compute on the fly
    csv_super = os.path.join(os.path.abspath(os.path.dirname(__file__)), "outputs", "data", "supersonic_tunnel_benchmarks.csv")
    csv_shock = os.path.join(os.path.abspath(os.path.dirname(__file__)), "outputs", "data", "shock_tube_benchmarks.csv")

    if os.path.exists(csv_super) and os.path.exists(csv_shock):
        df_super = pd.read_csv(csv_super)
        df_shock = pd.read_csv(csv_shock)
    else:
        st.warning("Benchmark CSVs not found. Please run generate_sample_runs.py first.")
        return

    st.markdown("#### 1. Supersonic Blow-Down Wind Tunnel Benchmarks (A = 0.04 m², P₀ = 20 bar, V = 10 m³)")
    st.dataframe(df_super, use_container_width=True)

    st.markdown("#### 2. Hypersonic Shock Tube Benchmarks (He driver into Air, P₁ = 10 kPa, L₄=3m, L₁=9m)")
    st.dataframe(df_shock, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🖼️ Compiled Benchmark Plots")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        p_mach = os.path.join(os.path.abspath(os.path.dirname(__file__)), "outputs", "plots", "mach_vs_nozzle_position.png")
        if os.path.exists(p_mach):
            st.image(p_mach, caption="Mach Number vs. Nozzle Position x/L for M=2.0, 3.0, 5.0")

    with col_p2:
        p_tank = os.path.join(os.path.abspath(os.path.dirname(__file__)), "outputs", "plots", "tank_pressure_vs_time.png")
        if os.path.exists(p_tank):
            st.image(p_tank, caption="Storage Tank Pressure Decay vs. Time (Isentropic Blow-Down)")

    col_p3, col_p4 = st.columns(2)
    with col_p3:
        p_xt = os.path.join(os.path.abspath(os.path.dirname(__file__)), "outputs", "plots", "shock_tube_xt_diagram_m3.png")
        if os.path.exists(p_xt):
            st.image(p_xt, caption="Shock Tube Wave Diagram (x-t) for Ms = 3.0")

    with col_p4:
        p_p4 = os.path.join(os.path.abspath(os.path.dirname(__file__)), "outputs", "plots", "diaphragm_pressure_ratio_vs_ms.png")
        if os.path.exists(p_p4):
            st.image(p_p4, caption="Diaphragm Pressure Ratio P4/P1 vs. Shock Mach Number")


if __name__ == "__main__":
    main()
