# Supersonic & Hypersonic Wind Tunnel Design & Runtime Calculator

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/restin-arch/High-Speed-Wind-Tunnel-Calculator/blob/main/Wind_Tunnel_Calculator_Colab.ipynb)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.66-brightgreen.svg)](https://streamlit.io/)

A complete aerodynamic design, sizing, and runtime estimation software package for high-speed wind tunnels and shock tubes.

Developed for **Wind Tunnel Techniques** course curriculum:
- **Module 2:** Supersonic Wind Tunnel Design & Blow-Down Runtime
- **Module 3:** Hypersonic Shock Tube / Runtime Calculations

---

## 🌟 Key Features

### 💨 Supersonic Blow-Down Wind Tunnel
- **Nozzle Sizing:** Inverts 1D Compressible Area-Mach relation to calculate exact choked throat area $A^*$, circular/planar dimensions, and contraction ratio.
- **Test-Section Flow Properties:** Calculates static pressure $P$, temperature $T$, density $\rho$, velocity $u$, dynamic pressure $q$, Sutherland viscosity $\mu(T)$, and unit Reynolds number $Re/m$.
- **Starting & Running Limits:** Computes normal shock total pressure ratio ($P_{02}/P_{01}$), starting pressure threshold ($P_{0,start}$), and minimum operating running pressure ($P_{0,min\_run}$) with diffuser efficiency.
- **Blow-Down Runtime Decay:** Models unsteady reservoir blow-down under adiabatic (isentropic), isothermal, and regulated pressure regimes.
- **Nozzle Aerodynamic Contour:** Computes convergent-divergent nozzle geometry with Prandtl-Meyer expansion angle limits and solves axial distributions $M(x/L)$, $P(x/L)/P_0$, and $T(x/L)/T_0$.

### ⚡ Hypersonic Shock Tube
- **Diaphragm Pressure Ratio ($P_4/P_1$):** Solves the non-linear 1D Riemann shock tube relation for target shock Mach number $M_s$.
- **Multi-Gas Support:** Helium ($\text{He}$), Nitrogen ($\text{N}_2$), Hydrogen ($\text{H}_2$), and Air with full thermodynamic properties.
- **Complete State Mapping (States 1–5):** Calculates pre-shock, post-shock, contact surface, driver expansion, and end-wall reflected shock conditions.
- **Wave Kinematics & Wave (x-t) Diagram:** Tracks incident shock, contact surface, expansion fan head and tail, and reflected expansion waves.
- **Usable Testing Window ($\Delta t_{test}$):** Computes exact test duration (ms) before driver contamination or expansion wave cutoff, with optimal driver-to-driven length sizing ($L_4/L_1$).

---

## 🚀 Quick Start Guide

### 1. Requirements & Installation
The project requires Python 3.10+ and standard scientific packages:
```bash
pip install numpy scipy matplotlib pandas streamlit
```

### 2. Launch the Desktop GUI (Tkinter)
Zero additional setup needed; runs natively on Windows, macOS, and Linux:
```bash
python app_gui_tk.py
```

### 3. Launch the Web Dashboard (Streamlit)
Interactive modern web application with reactive sliders, live metric cards, and high-res plots:
```bash
python -m streamlit run app_streamlit.py
```

### 4. Command-Line Interface (CLI)
Instant calculations and scripting directly from terminal:
```bash
# Supersonic Blow-Down Tunnel Calculation:
python cli.py supersonic --mach 2.5 --area 0.04 --p0 20.0 --volume 10.0

# Hypersonic Shock Tube Calculation:
python cli.py shocktube --mach 3.0 --driver He --driven Air --p1 10.0

# Interactive CLI Menu:
python cli.py
```

### 5. Run Verification & Unit Tests
```bash
python tests/test_gas_dynamics.py
```

### 6. Generate Benchmark Runs (M = 2.0, 3.0, 5.0)
```bash
python generate_sample_runs.py
```

---

## 📊 Benchmark Outputs (M = 2.0, 3.0, 5.0)

Pre-computed datasets and publication figures are stored in `outputs/`:
- **Plots (`outputs/plots/`):**
  - `mach_vs_nozzle_position.png`: Mach number distribution $M(x/L)$ for $M=2, 3, 5$.
  - `nozzle_contours_geometry.png`: Aerodynamic convergent-divergent nozzle wall contours.
  - `tank_pressure_vs_time.png`: Storage tank pressure decay $P_0(t)$ vs time during blow-down.
  - `shock_tube_xt_diagram_m3.png`: Wave ($x-t$) diagram with shaded usable testing window for $M_s=3.0$.
  - `diaphragm_pressure_ratio_vs_ms.png`: $P_4/P_1$ sensitivity curves for Helium vs Nitrogen drivers.
- **Data Tables (`outputs/data/`):**
  - `supersonic_tunnel_benchmarks.csv`
  - `shock_tube_benchmarks.csv`

---

## 📁 Repository Structure

```
Wind Tunnel Technique/
├── core/
│   ├── __init__.py            # Unified package exports
│   ├── gas_dynamics.py        # Isentropic flow, normal shocks, gas properties
│   ├── supersonic_tunnel.py   # Nozzle sizing, blow-down decay, runtime solver
│   ├── shock_tube.py          # Shock tube relation, states 1-5, wave kinematics
│   └── nozzle_contour.py      # Nozzle aerodynamic geometry & axial M(x/L) solver
├── app_gui_tk.py              # Standalone Desktop GUI (Tkinter + Matplotlib)
├── app_streamlit.py           # Reactive Web Dashboard (Streamlit)
├── cli.py                     # Command-line interface with interactive & batch modes
├── generate_sample_runs.py    # Batch benchmark generator for M=2, 3, 5
├── tests/
│   └── test_gas_dynamics.py   # Physics unit tests and validation
├── outputs/
│   ├── plots/                 # High-resolution PNG figures
│   └── data/                  # Benchmark CSV data tables
├── reports/
│   └── FINAL_PROJECT_REPORT.md# Detailed technical project report
└── README.md                  # Project overview & documentation
```

---

## 📖 Technical Project Report
See [FINAL_PROJECT_REPORT.md](reports/FINAL_PROJECT_REPORT.md) for full theoretical derivations, governing equations, verification against NACA 1135 / Anderson, and detailed aerodynamic discussions.
