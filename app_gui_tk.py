"""
Tkinter Native Desktop GUI Application
======================================
Supersonic & Hypersonic Wind Tunnel Design & Runtime Calculator
Features:
  - Supersonic Blow-Down Wind Tunnel (Nozzle sizing, flow states, tank decay, runtime)
  - Hypersonic Shock Tube (P4/P1 ratio, states 1-5, x-t wave diagram, usable testing window)
"""

import sys
import os
import math
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np

# Matplotlib embedding for Tkinter
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core import (
    calculate_supersonic_tunnel,
    calculate_shock_tube,
    generate_nozzle_contour,
    GAS_DATABASE
)


class WindTunnelApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("High-Speed Wind Tunnel & Shock Tube Calculator")
        self.geometry("1240x840")
        self.minsize(1050, 720)

        # Apply a clean modern TTK theme
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Configure custom styling
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[12, 6])
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#1a365d")
        style.configure("SubHeader.TLabel", font=("Segoe UI", 10, "italic"), foreground="#4a5568")
        style.configure("Card.TFrame", background="#f8fafc", relief="solid", borderwidth=1)
        style.configure("Calc.TButton", font=("Segoe UI", 10, "bold"), background="#2b6cb0", foreground="white")
        style.map("Calc.TButton", background=[("active", "#2c5282")])

        # Main notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Tab 1: Supersonic Wind Tunnel
        self.tab_supersonic = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_supersonic, text="  Supersonic Blow-Down Tunnel  ")
        self.build_supersonic_tab()

        # Tab 2: Hypersonic Shock Tube
        self.tab_shocktube = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_shocktube, text="  Hypersonic Shock Tube  ")
        self.build_shocktube_tab()

        # Initial trigger
        self.calculate_supersonic()
        self.calculate_shocktube()

    # ==========================================================================
    # TAB 1: SUPERSONIC BLOW-DOWN WIND TUNNEL
    # ==========================================================================
    def build_supersonic_tab(self):
        main_pane = ttk.PanedWindow(self.tab_supersonic, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # Left panel: Inputs & Results
        left_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(left_frame, weight=1)

        # Header
        ttk.Label(left_frame, text="Supersonic Blow-Down Sizing", style="Header.TLabel").pack(anchor="w")
        ttk.Label(left_frame, text="1D Isentropic Nozzle Sizing & Tank Depletion Runtime", style="SubHeader.TLabel").pack(anchor="w", pady=(0, 10))

        # Inputs Card
        in_group = ttk.LabelFrame(left_frame, text="Input Parameters", padding=10)
        in_group.pack(fill=tk.X, pady=5)

        self.ss_mach_var = tk.DoubleVar(value=2.5)
        self.ss_area_var = tk.DoubleVar(value=0.04)        # 0.2m x 0.2m
        self.ss_p0_bar_var = tk.DoubleVar(value=15.0)      # 15 bar
        self.ss_v_tank_var = tk.DoubleVar(value=10.0)      # 10 m^3
        self.ss_t0_var = tk.DoubleVar(value=300.0)         # 300 K
        self.ss_pback_var = tk.DoubleVar(value=1.01325)    # bar

        row = 0
        def add_input_row(parent, label_text, var, unit, r):
            ttk.Label(parent, text=label_text).grid(row=r, column=0, sticky="w", pady=3)
            entry = ttk.Entry(parent, textvariable=var, width=10)
            entry.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
            ttk.Label(parent, text=unit, foreground="#718096").grid(row=r, column=2, sticky="w", pady=3)

        add_input_row(in_group, "Test Mach Number (M):", self.ss_mach_var, "-", row); row += 1
        add_input_row(in_group, "Test Section Area (A):", self.ss_area_var, "m²", row); row += 1
        add_input_row(in_group, "Tank Initial P₀:", self.ss_p0_bar_var, "bar", row); row += 1
        add_input_row(in_group, "Tank Volume (V):", self.ss_v_tank_var, "m³", row); row += 1
        add_input_row(in_group, "Tank Temp (T₀):", self.ss_t0_var, "K", row); row += 1
        add_input_row(in_group, "Back Pressure (P_a):", self.ss_pback_var, "bar", row); row += 1

        in_group.columnconfigure(1, weight=1)

        btn_calc = ttk.Button(left_frame, text="Calculate & Update Plots", style="Calc.TButton", command=self.calculate_supersonic)
        btn_calc.pack(fill=tk.X, pady=10)

        # Results Display Card
        res_group = ttk.LabelFrame(left_frame, text="Calculated Aerodynamic Sizing & Runtime", padding=10)
        res_group.pack(fill=tk.BOTH, expand=True, pady=5)

        self.ss_results_tree = ttk.Treeview(res_group, columns=("param", "value"), show="tree", selectmode="none", height=14)
        self.ss_results_tree.pack(fill=tk.BOTH, expand=True)
        self.ss_results_tree.column("#0", width=180, anchor="w")
        self.ss_results_tree.column("param", width=0, stretch=tk.NO)
        self.ss_results_tree.column("value", width=150, anchor="e")

        # Right panel: Embedded Matplotlib Plots
        right_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(right_frame, weight=3)

        self.fig_ss = Figure(figsize=(7, 6.5), dpi=100)
        self.ax_ss1 = self.fig_ss.add_subplot(2, 1, 1)
        self.ax_ss2 = self.fig_ss.add_subplot(2, 1, 2)
        self.fig_ss.tight_layout(pad=3.0)

        self.canvas_ss = FigureCanvasTkAgg(self.fig_ss, master=right_frame)
        self.canvas_ss.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_ss = NavigationToolbar2Tk(self.canvas_ss, right_frame)
        toolbar_ss.update()

    def calculate_supersonic(self):
        try:
            M = self.ss_mach_var.get()
            A = self.ss_area_var.get()
            P0_bar = self.ss_p0_bar_var.get()
            V = self.ss_v_tank_var.get()
            T0 = self.ss_t0_var.get()
            Pa_bar = self.ss_pback_var.get()

            res = calculate_supersonic_tunnel(
                mach=M,
                test_area=A,
                tank_pressure_init=P0_bar * 1e5,
                tank_volume=V,
                tank_temp_init=T0,
                back_pressure=Pa_bar * 1e5
            )
            noz = generate_nozzle_contour(mach_design=M, test_area=A)

            # Update Treeview results
            self.ss_results_tree.delete(*self.ss_results_tree.get_children())
            items = [
                ("Geometric Sizing", ""),
                ("  Area Ratio (A / A*)", f"{res.area_ratio:.4f}"),
                ("  Throat Area (A*)", f"{res.throat_area * 1e4:.2f} cm²"),
                ("  Equiv. Throat Diam.", f"{res.throat_diameter_equiv * 100:.2f} cm"),
                ("  Equiv. Test Diam.", f"{res.test_diameter_equiv * 100:.2f} cm"),
                ("Test Section Flow (t = 0)", ""),
                ("  Initial Mass Flow (ṁ)", f"{res.mass_flow_rate_init:.2f} kg/s"),
                ("  Static Pressure (P)", f"{res.static_pressure / 1e3:.2f} kPa"),
                ("  Static Temperature (T)", f"{res.static_temp:.1f} K"),
                ("  Flow Velocity (u)", f"{res.flow_velocity:.1f} m/s"),
                ("  Dynamic Pressure (q)", f"{res.dynamic_pressure / 1e3:.2f} kPa"),
                ("  Unit Reynolds Number", f"{res.unit_reynolds_per_meter / 1e6:.2f} × 10⁶ /m"),
                ("Pressure Limits & Runtime", ""),
                ("  Starting P₀ Required", f"{res.p0_starting / 1e5:.2f} bar"),
                ("  Min. Running P₀", f"{res.p0_min_running / 1e5:.2f} bar"),
                ("  Run Duration (Adiabatic)", f"{res.runtime_adiabatic_to_run:.2f} s"),
                ("  Run Duration (Isothermal)", f"{res.runtime_isothermal_to_run:.2f} s"),
                ("  Run Duration (Regulated)", f"{res.runtime_regulated:.2f} s")
            ]
            for label, val in items:
                self.ss_results_tree.insert("", tk.END, text=label, values=(val,))

            # Plot 1: Mach number vs Nozzle position
            self.ax_ss1.clear()
            self.ax_ss1.plot(noz.x_normalized, noz.mach_distribution, color="#1e40af", linewidth=2.2, label=f"Mach Profile M(x/L)")
            idx_th = np.argmin(np.abs(noz.x_coords))
            self.ax_ss1.plot(noz.x_normalized[idx_th], 1.0, "ro", label="Throat ($M=1.0$)")
            self.ax_ss1.axhline(1.0, color="gray", linestyle=":", alpha=0.6)
            self.ax_ss1.set_xlabel("Normalized Nozzle Axial Position, $x / L$")
            self.ax_ss1.set_ylabel("Mach Number, $M$")
            self.ax_ss1.set_title(f"Mach Number vs. Nozzle Position (Exit $M={M:.2f}$)")
            self.ax_ss1.grid(True, alpha=0.4)
            self.ax_ss1.legend(loc="upper left")

            # Plot 2: Tank Pressure vs Time
            self.ax_ss2.clear()
            t_s = res.time_array
            p0_bar_arr = res.p0_time_adiabatic / 1e5
            self.ax_ss2.plot(t_s, p0_bar_arr, color="#b91c1c", linewidth=2.2, label="Adiabatic Tank $P_0(t)$")
            self.ax_ss2.axhline(res.p0_starting / 1e5, color="orange", linestyle="--", label=f"$P_{{0,start}} = {res.p0_starting/1e5:.2f}$ bar")
            self.ax_ss2.axhline(res.p0_min_running / 1e5, color="purple", linestyle=":", label=f"$P_{{0,run}} = {res.p0_min_running/1e5:.2f}$ bar")
            if res.runtime_adiabatic_to_run > 0:
                self.ax_ss2.plot(res.runtime_adiabatic_to_run, res.p0_min_running / 1e5, "ks", markersize=6, label=f"Cutoff $t_{{run}}={res.runtime_adiabatic_to_run:.1f}$ s")
            self.ax_ss2.set_xlabel("Time, $t$ (seconds)")
            self.ax_ss2.set_ylabel("Tank Stagnation Pressure $P_0$ (bar)")
            self.ax_ss2.set_title("Tank Pressure Decay vs. Time (Blow-Down)")
            self.ax_ss2.grid(True, alpha=0.4)
            self.ax_ss2.legend(loc="upper right", fontsize=8)

            self.fig_ss.tight_layout(pad=2.0)
            self.canvas_ss.draw()

        except Exception as e:
            messagebox.showerror("Calculation Error", str(e))

    # ==========================================================================
    # TAB 2: HYPERSONIC SHOCK TUBE
    # ==========================================================================
    def build_shocktube_tab(self):
        main_pane = ttk.PanedWindow(self.tab_shocktube, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Hypersonic Shock Tube Analysis", style="Header.TLabel").pack(anchor="w")
        ttk.Label(left_frame, text="Pressure Ratio Sizing, Wave Kinematics & Testing Window", style="SubHeader.TLabel").pack(anchor="w", pady=(0, 10))

        in_group = ttk.LabelFrame(left_frame, text="Shock Tube Parameters", padding=10)
        in_group.pack(fill=tk.X, pady=5)

        self.sh_mach_var = tk.DoubleVar(value=3.0)
        self.sh_driver_gas_var = tk.StringVar(value="He")
        self.sh_driven_gas_var = tk.StringVar(value="Air")
        self.sh_p1_kpa_var = tk.DoubleVar(value=10.0)      # 10 kPa
        self.sh_t1_var = tk.DoubleVar(value=300.0)         # 300 K
        self.sh_t4_var = tk.DoubleVar(value=300.0)         # 300 K
        self.sh_l4_var = tk.DoubleVar(value=3.0)           # 3 m driver
        self.sh_l1_var = tk.DoubleVar(value=9.0)           # 9 m driven

        r = 0
        ttk.Label(in_group, text="Target Shock Mach (Mₛ):").grid(row=r, column=0, sticky="w", pady=3)
        ttk.Entry(in_group, textvariable=self.sh_mach_var, width=10).grid(row=r, column=1, sticky="ew", padx=6, pady=3)
        ttk.Label(in_group, text="-", foreground="#718096").grid(row=r, column=2, sticky="w", pady=3); r += 1

        ttk.Label(in_group, text="Driver Gas:").grid(row=r, column=0, sticky="w", pady=3)
        cb_driver = ttk.Combobox(in_group, textvariable=self.sh_driver_gas_var, values=["He", "N2", "H2", "Air"], width=8, state="readonly")
        cb_driver.grid(row=r, column=1, sticky="ew", padx=6, pady=3); r += 1

        ttk.Label(in_group, text="Driven Gas:").grid(row=r, column=0, sticky="w", pady=3)
        cb_driven = ttk.Combobox(in_group, textvariable=self.sh_driven_gas_var, values=["Air", "N2", "CO2", "Ar"], width=8, state="readonly")
        cb_driven.grid(row=r, column=1, sticky="ew", padx=6, pady=3); r += 1

        def add_st_row(label, var, unit, row_idx):
            ttk.Label(in_group, text=label).grid(row=row_idx, column=0, sticky="w", pady=3)
            ttk.Entry(in_group, textvariable=var, width=10).grid(row=row_idx, column=1, sticky="ew", padx=6, pady=3)
            ttk.Label(in_group, text=unit, foreground="#718096").grid(row=row_idx, column=2, sticky="w", pady=3)

        add_st_row("Driven Pressure (P₁):", self.sh_p1_kpa_var, "kPa", r); r += 1
        add_st_row("Driven Temp (T₁):", self.sh_t1_var, "K", r); r += 1
        add_st_row("Driver Temp (T₄):", self.sh_t4_var, "K", r); r += 1
        add_st_row("Driver Length (L₄):", self.sh_l4_var, "m", r); r += 1
        add_st_row("Driven Length (L₁):", self.sh_l1_var, "m", r); r += 1

        in_group.columnconfigure(1, weight=1)

        btn_calc_sh = ttk.Button(left_frame, text="Calculate & Plot Waves", style="Calc.TButton", command=self.calculate_shocktube)
        btn_calc_sh.pack(fill=tk.X, pady=10)

        # Treeview outputs
        res_group = ttk.LabelFrame(left_frame, text="Shock Wave & Test Window Properties", padding=10)
        res_group.pack(fill=tk.BOTH, expand=True, pady=5)

        self.sh_results_tree = ttk.Treeview(res_group, columns=("param", "value"), show="tree", selectmode="none", height=14)
        self.sh_results_tree.pack(fill=tk.BOTH, expand=True)
        self.sh_results_tree.column("#0", width=180, anchor="w")
        self.sh_results_tree.column("param", width=0, stretch=tk.NO)
        self.sh_results_tree.column("value", width=150, anchor="e")

        # Right panel: Shock Tube Plots
        right_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(right_frame, weight=3)

        self.fig_sh = Figure(figsize=(7, 6.5), dpi=100)
        self.ax_sh1 = self.fig_sh.add_subplot(2, 1, 1)
        self.ax_sh2 = self.fig_sh.add_subplot(2, 1, 2)
        self.fig_sh.tight_layout(pad=3.0)

        self.canvas_sh = FigureCanvasTkAgg(self.fig_sh, master=right_frame)
        self.canvas_sh.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_sh = NavigationToolbar2Tk(self.canvas_sh, right_frame)
        toolbar_sh.update()

    def calculate_shocktube(self):
        try:
            Ms = self.sh_mach_var.get()
            driver = self.sh_driver_gas_var.get()
            driven = self.sh_driven_gas_var.get()
            P1_Pa = self.sh_p1_kpa_var.get() * 1e3
            T1 = self.sh_t1_var.get()
            T4 = self.sh_t4_var.get()
            L4 = self.sh_l4_var.get()
            L1 = self.sh_l1_var.get()

            sh = calculate_shock_tube(
                shock_mach=Ms,
                driver_gas=driver,
                driven_gas=driven,
                p1=P1_Pa,
                t1=T1,
                t4=T4,
                driver_length=L4,
                driven_length=L1
            )

            # Update Treeview results
            self.sh_results_tree.delete(*self.sh_results_tree.get_children())
            items = [
                ("Diaphragm Pressure Ratio", ""),
                ("  Pressure Ratio (P₄ / P₁)", f"{sh.p4_over_p1:.2f}"),
                ("  Required Driver P₄", f"{sh.p4 / 1e5:.2f} bar"),
                ("  Theoretical Max Mₛ", f"{sh.ms_limit:.2f}"),
                ("Wave Speeds", ""),
                ("  Incident Shock (Wₛ)", f"{sh.w_shock:.1f} m/s"),
                ("  Induced Velocity (u₂)", f"{sh.u2:.1f} m/s"),
                ("  Reflected Shock (W_R)", f"{sh.w_reflected:.1f} m/s"),
                ("State 2 (Behind Incident Shock)", ""),
                ("  Pressure (P₂)", f"{sh.p2 / 1e3:.2f} kPa"),
                ("  Temperature (T₂)", f"{sh.t2:.1f} K"),
                ("  Density (ρ₂)", f"{sh.rho2:.3f} kg/m³"),
                ("State 5 (End-Wall Reservoir)", ""),
                ("  Pressure (P₅)", f"{sh.p5 / 1e3:.2f} kPa"),
                ("  Temperature (T₅)", f"{sh.t5:.1f} K"),
                ("Testing Window & Sizing", ""),
                ("  Usable Test Time (Δt)", f"{sh.usable_test_window_ms:.2f} ms"),
                ("  Limiting Factor", f"{sh.test_limiting_factor}"),
                ("  Optimal L₄ / L₁ Ratio", f"{sh.optimum_length_ratio:.3f}"),
                ("  Recommended Driver L₄", f"{sh.optimum_driver_length:.2f} m")
            ]
            for label, val in items:
                self.sh_results_tree.insert("", tk.END, text=label, values=(val,))

            # Plot 1: Wave (x-t) Diagram
            self.ax_sh1.clear()
            wp = sh.wave_paths
            self.ax_sh1.axvline(-sh.driver_length, color="black", linewidth=2.0)
            self.ax_sh1.axvline(0.0, color="gray", linestyle="--", linewidth=1.2)
            self.ax_sh1.axvline(sh.driven_length, color="black", linewidth=2.0)

            self.ax_sh1.plot(wp["Incident Shock"][0], wp["Incident Shock"][1] * 1000, "r-", linewidth=2.0, label="Incident Shock")
            self.ax_sh1.plot(wp["Contact Surface"][0], wp["Contact Surface"][1] * 1000, "b--", linewidth=1.8, label="Contact Surface")
            self.ax_sh1.plot(wp["Reflected Shock"][0], wp["Reflected Shock"][1] * 1000, "m-.", linewidth=1.8, label="Reflected Shock")
            self.ax_sh1.plot(wp["Expansion Head"][0], wp["Expansion Head"][1] * 1000, "c-", linewidth=1.5, label="Expansion Head")
            self.ax_sh1.plot(wp["Reflected Expansion"][0], wp["Reflected Expansion"][1] * 1000, "g-.", linewidth=1.5, label="Refl. Expansion")

            # Shade test window
            t_shock_ms = sh.time_shock_arrival * 1000
            t_win_ms = sh.usable_test_window_ms
            self.ax_sh1.axvspan(sh.driven_length - 0.3, sh.driven_length, ymin=t_shock_ms/30.0, ymax=(t_shock_ms+t_win_ms)/30.0, color="yellow", alpha=0.6)

            self.ax_sh1.set_xlabel("Tube Position $x$ (m)")
            self.ax_sh1.set_ylabel("Time $t$ (ms)")
            self.ax_sh1.set_title(f"Wave Diagram (x-t) for $M_s={sh.shock_mach:.1f}$ (Test Window: {sh.usable_test_window_ms:.2f} ms)")
            self.ax_sh1.grid(True, alpha=0.4)
            self.ax_sh1.legend(loc="upper left", fontsize=8)
            self.ax_sh1.set_ylim(0, max(25.0, (t_shock_ms + t_win_ms) * 1.5))

            # Plot 2: P4/P1 vs Ms Sensitivity
            self.ax_sh2.clear()
            ms_vals = np.linspace(1.2, min(5.5, sh.ms_limit - 0.1), 100)
            p4p1_curve = []
            for m in ms_vals:
                try:
                    s_tmp = calculate_shock_tube(m, driver, driven, P1_Pa, T1, T4, L4, L1)
                    p4p1_curve.append(s_tmp.p4_over_p1)
                except Exception:
                    p4p1_curve.append(np.nan)

            self.ax_sh2.semilogy(ms_vals, p4p1_curve, color="#059669", linewidth=2.0, label=f"{driver} into {driven}")
            self.ax_sh2.plot(sh.shock_mach, sh.p4_over_p1, "ro", markersize=6, label=f"Current $M_s={sh.shock_mach:.1f}$")
            self.ax_sh2.set_xlabel("Shock Mach Number $M_s$")
            self.ax_sh2.set_ylabel("Pressure Ratio $P_4 / P_1$")
            self.ax_sh2.set_title("Required Diaphragm Pressure Ratio vs. $M_s$")
            self.ax_sh2.grid(True, which="both", alpha=0.4)
            self.ax_sh2.legend(loc="upper left")

            self.fig_sh.tight_layout(pad=2.0)
            self.canvas_sh.draw()

        except Exception as e:
            messagebox.showerror("Shock Tube Calculation Error", str(e))


if __name__ == "__main__":
    app = WindTunnelApp()
    app.mainloop()
