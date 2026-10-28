"""
Command-Line Interface (CLI)
============================
High-Speed Wind Tunnel & Shock Tube Calculator.
Provides instant terminal calculations, batch runs, and interactive prompts.
"""

import argparse
import sys
import os

# Enable UTF-8 encoding for Windows console
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core import (
    calculate_supersonic_tunnel,
    calculate_shock_tube,
    generate_nozzle_contour
)
from generate_sample_runs import run_benchmark_cases


def print_banner():
    print("""
========================================================================
   SUPERSONIC & HYPERSONIC WIND TUNNEL DESIGN & RUNTIME CALCULATOR
                  Modules 2 & 3 Aerodynamics Suite
========================================================================
    """)


def handle_supersonic(args):
    print("\n--- Supersonic Blow-Down Wind Tunnel (Module 2) ---")
    res = calculate_supersonic_tunnel(
        mach=args.mach,
        test_area=args.area,
        tank_pressure_init=args.p0 * 1e5,
        tank_volume=args.volume,
        tank_temp_init=args.t0,
        back_pressure=args.pback * 1e5,
        gas_name=args.gas
    )

    print(f"Design Mach Number (M):          {res.mach:.2f}")
    print(f"Working Gas:                     {res.gas_name}")
    print(f"Test Section Area (A):           {res.test_area * 1e4:.2f} cm^2 ({res.test_area:.4f} m^2)")
    print(f"Area-Mach Ratio (A/A*):          {res.area_ratio:.4f}")
    print(f"Required Throat Area (A*):       {res.throat_area * 1e4:.2f} cm^2 ({res.throat_area:.6f} m^2)")
    print(f"Equiv. Throat Diameter (D*):     {res.throat_diameter_equiv * 100:.2f} cm")
    print(f"-" * 55)
    print(f"Initial Mass Flow Rate (m_dot):  {res.mass_flow_rate_init:.2f} kg/s")
    print(f"Test Section Static Temp (T):    {res.static_temp:.1f} K ({res.static_temp - 273.15:.1f} C)")
    print(f"Test Section Static Press (P):   {res.static_pressure / 1e3:.2f} kPa ({res.static_pressure / 1e5:.3f} bar)")
    print(f"Test Section Flow Velocity (u):  {res.flow_velocity:.1f} m/s")
    print(f"Dynamic Pressure (q):            {res.dynamic_pressure / 1e3:.2f} kPa")
    print(f"Unit Reynolds Number (Re/m):     {res.unit_reynolds_per_meter / 1e6:.2f} x 10^6 /m")
    print(f"-" * 55)
    print(f"Starting Pressure Required (P0): {res.p0_starting / 1e5:.2f} bar")
    print(f"Min. Running Pressure (P0_run):  {res.p0_min_running / 1e5:.2f} bar")
    print(f"Total Runtime (Adiabatic):       {res.runtime_adiabatic_to_run:.2f} seconds")
    print(f"Total Runtime (Isothermal):      {res.runtime_isothermal_to_run:.2f} seconds")
    print(f"Total Runtime (Regulated):       {res.runtime_regulated:.2f} seconds")
    print(f"=" * 55)


def handle_shocktube(args):
    print("\n--- Hypersonic Shock Tube / Runtime Calculator (Module 3) ---")
    sh = calculate_shock_tube(
        shock_mach=args.mach,
        driver_gas=args.driver,
        driven_gas=args.driven,
        p1=args.p1 * 1e3,
        t1=args.t1,
        t4=args.t4,
        driver_length=args.l4,
        driven_length=args.l1,
        test_position=args.xts
    )

    print(f"Target Incident Shock Mach (Ms): {sh.shock_mach:.2f}")
    print(f"Driver Gas:                      {sh.driver_gas} at {sh.t4:.1f} K")
    print(f"Driven Gas:                      {sh.driven_gas} at {sh.t1:.1f} K, {sh.p1 / 1e3:.1f} kPa")
    print(f"Theoretical Max Mach Ceiling:    {sh.ms_limit:.2f}")
    print(f"-" * 55)
    print(f"Diaphragm Pressure Ratio (P4/P1):{sh.p4_over_p1:.2f}")
    print(f"Required Driver Pressure (P4):   {sh.p4 / 1e5:.2f} bar ({sh.p4 / 1e3:.1f} kPa)")
    print(f"Incident Shock Speed (Ws):       {sh.w_shock:.1f} m/s")
    print(f"Induced Flow Velocity (u2):      {sh.u2:.1f} m/s")
    print(f"Post-Shock Temp (T2):            {sh.t2:.1f} K ({sh.t2 - 273.15:.1f} C)")
    print(f"Post-Shock Pressure (P2):        {sh.p2 / 1e3:.2f} kPa")
    print(f"Reflected Shock Temp (T5):       {sh.t5:.1f} K ({sh.t5 - 273.15:.1f} C)")
    print(f"Reflected Shock Pressure (P5):   {sh.p5 / 1e3:.2f} kPa ({sh.p5 / 1e5:.2f} bar)")
    print(f"-" * 55)
    print(f"Usable Testing Window (dt):      {sh.usable_test_window_ms:.2f} ms")
    print(f"Limiting Boundary:               {sh.test_limiting_factor}")
    print(f"Recommended Driver Length (L4):  {sh.optimum_driver_length:.2f} m (Ratio L4/L1 = {sh.optimum_length_ratio:.3f})")
    print(f"=" * 55)


def interactive_mode():
    print_banner()
    print("Select an option:")
    print("  1. Supersonic Blow-Down Wind Tunnel (Module 2)")
    print("  2. Hypersonic Shock Tube / Runtime Calculator (Module 3)")
    print("  3. Run Day 4 Benchmark Cases (M = 2.0, 3.0, 5.0)")
    print("  4. Launch Desktop GUI (Tkinter)")
    print("  5. Launch Web GUI (Streamlit)")
    print("  0. Exit")

    choice = input("\nEnter choice (0-5): ").strip()
    if choice == "1":
        m_str = input("Test Mach Number [2.5]: ").strip() or "2.5"
        a_str = input("Test Area (m²) [0.04]: ").strip() or "0.04"
        p_str = input("Tank Pressure (bar) [20.0]: ").strip() or "20.0"
        v_str = input("Tank Volume (m³) [10.0]: ").strip() or "10.0"

        class DummyArgs:
            mach = float(m_str)
            area = float(a_str)
            p0 = float(p_str)
            volume = float(v_str)
            t0 = 300.0
            pback = 1.01325
            gas = "Air"

        handle_supersonic(DummyArgs())

    elif choice == "2":
        m_str = input("Target Shock Mach [3.0]: ").strip() or "3.0"
        dr_str = input("Driver Gas (He, N2, H2, Air) [He]: ").strip() or "He"
        dn_str = input("Driven Gas (Air, N2, CO2) [Air]: ").strip() or "Air"
        p1_str = input("Driven Pressure P₁ (kPa) [10.0]: ").strip() or "10.0"

        class DummyArgsST:
            mach = float(m_str)
            driver = dr_str
            driven = dn_str
            p1 = float(p1_str)
            t1 = 300.0
            t4 = 300.0
            l4 = 3.0
            l1 = 9.0
            xts = 9.0

        handle_shocktube(DummyArgsST())

    elif choice == "3":
        run_benchmark_cases()
    elif choice == "4":
        from app_gui_tk import WindTunnelApp
        app = WindTunnelApp()
        app.mainloop()
    elif choice == "5":
        import subprocess
        subprocess.run(["streamlit", "run", "app_streamlit.py"])


def main():
    parser = argparse.ArgumentParser(description="Supersonic & Hypersonic Wind Tunnel Design & Runtime Calculator")
    subparsers = parser.add_subparsers(dest="command")

    # Supersonic parser
    sp_super = subparsers.add_parser("supersonic", help="Supersonic Blow-Down Wind Tunnel Module")
    sp_super.add_argument("--mach", type=float, default=2.5, help="Test section Mach number (default 2.5)")
    sp_super.add_argument("--area", type=float, default=0.04, help="Test section area in m^2 (default 0.04)")
    sp_super.add_argument("--p0", type=float, default=20.0, help="Storage tank pressure in bar (default 20.0)")
    sp_super.add_argument("--volume", type=float, default=10.0, help="Storage tank volume in m^3 (default 10.0)")
    sp_super.add_argument("--t0", type=float, default=300.0, help="Tank temperature in K (default 300.0)")
    sp_super.add_argument("--pback", type=float, default=1.01325, help="Back pressure in bar (default 1.01325)")
    sp_super.add_argument("--gas", type=str, default="Air", help="Gas name (default Air)")

    # Shock tube parser
    sp_shock = subparsers.add_parser("shocktube", help="Hypersonic Shock Tube Module")
    sp_shock.add_argument("--mach", type=float, default=3.0, help="Target incident shock Mach number (default 3.0)")
    sp_shock.add_argument("--driver", type=str, default="He", help="Driver gas name (default He)")
    sp_shock.add_argument("--driven", type=str, default="Air", help="Driven gas name (default Air)")
    sp_shock.add_argument("--p1", type=float, default=10.0, help="Driven gas pressure P1 in kPa (default 10.0)")
    sp_shock.add_argument("--t1", type=float, default=300.0, help="Driven gas temperature in K (default 300.0)")
    sp_shock.add_argument("--t4", type=float, default=300.0, help="Driver gas temperature in K (default 300.0)")
    sp_shock.add_argument("--l4", type=float, default=3.0, help="Driver section length in m (default 3.0)")
    sp_shock.add_argument("--l1", type=float, default=9.0, help="Driven section length in m (default 9.0)")
    sp_shock.add_argument("--xts", type=float, default=9.0, help="Test station position in m (default 9.0)")

    # Batch parser
    subparsers.add_parser("batch", help="Run benchmark cases for M = 2, 3, 5")

    args = parser.parse_args()

    if args.command == "supersonic":
        handle_supersonic(args)
    elif args.command == "shocktube":
        handle_shocktube(args)
    elif args.command == "batch":
        run_benchmark_cases()
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
