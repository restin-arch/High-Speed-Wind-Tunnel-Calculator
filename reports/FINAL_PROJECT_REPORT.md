# High-Speed Aerodynamics Project Report
## Supersonic & Hypersonic Wind Tunnel Design & Runtime Calculator (Python / MATLAB)

**Course / Subject:** Wind Tunnel Techniques  
**Core Aerodynamic Domains Covered:** 
- **Supersonic Wind Tunnel:** Nozzle Sizing, Flow Aerodynamics & Blow-Down Runtime Analysis
- **Hypersonic Shock Tube:** Diaphragm Pressure Ratio, Multi-State Thermodynamics & Usable Testing Window
**Date:** October 2026  
**Status:** Completed & Validated

---

## 1. Executive Summary

High-speed ground testing facilities (supersonic wind tunnels and hypersonic shock tubes) operate on transient fluid dynamic principles requiring precise aerodynamic sizing and runtime predictions. This project presents an automated, dual-interface computational toolkit developed in Python that models:

1. **Supersonic Blow-Down Wind Tunnels:** Automating convergent-divergent nozzle throat sizing ($A^*$), test-section flow states ($P, T, \rho, u, q, Re/m$), tunnel starting and unchoking pressure limits, and reservoir blow-down pressure decay $P_0(t)$ across adiabatic, isothermal, and regulated regimes.
2. **Hypersonic Shock Tubes:** Solving the non-linear diaphragm pressure ratio equation ($P_4/P_1$), complete thermodynamic state mapping (States 1 through 5), wave propagation speeds ($W_s, u_2, W_R, a_4, u_3-a_3$), driver-to-driven section sizing optimization, and exact usable testing window ($\Delta t_{test}$) prediction before wave interference.
3. **Multi-Platform User Interfaces:** Featuring both a lightweight, zero-dependency **Desktop GUI (Tkinter + Matplotlib)** and a modern **Reactive Web Dashboard (Streamlit)**, alongside a fully scriptable **Command-Line Interface (CLI)**.
4. **Benchmark Suite ($M = 2.0, 3.0, 5.0$):** Validated against standard compressible flow theory (NACA Report 1135 and Anderson's *Modern Compressible Flow*).

---

## 2. Theoretical Framework & Governing Equations

### 2.1 Supersonic Blow-Down Wind Tunnel

#### 2.1.1 1D Compressible Isentropic Flow & Nozzle Sizing
For steady, 1D isentropic flow of a calorically perfect gas with specific heat ratio $\gamma$:

- **Stagnation Temperature and Pressure Ratios:**
  $$\frac{T}{T_0} = \left( 1 + \frac{\gamma - 1}{2} M^2 \right)^{-1}$$
  $$\frac{P}{P_0} = \left( 1 + \frac{\gamma - 1}{2} M^2 \right)^{-\frac{\gamma}{\gamma - 1}}$$
  $$\frac{\rho}{\rho_0} = \left( 1 + \frac{\gamma - 1}{2} M^2 \right)^{-\frac{1}{\gamma - 1}}$$

- **Area-Mach Relation (Throat Sizing):**
  $$\frac{A}{A^*} = \frac{1}{M} \left[ \frac{2}{\gamma + 1} \left( 1 + \frac{\gamma - 1}{2} M^2 \right) \right]^{\frac{\gamma + 1}{2(\gamma - 1)}}$$
  Given the test-section area $A_{test}$ and design Mach $M$, the choked throat area is:
  $$A^* = \frac{A_{test}}{(A / A^*)}$$

- **Choked Mass Flow Rate:**
  At the sonic throat ($M = 1$), the choked mass flow rate $\dot{m}$ is dictated by stagnation conditions:
  $$\dot{m}(t) = C^* \frac{P_0(t) A^*}{\sqrt{T_0(t)}} = \sqrt{\frac{\gamma}{R}} \left( \frac{2}{\gamma + 1} \right)^{\frac{\gamma + 1}{2(\gamma - 1)}} \frac{P_0(t) A^*}{\sqrt{T_0(t)}}$$

- **Dynamic Viscosity & Unit Reynolds Number:**
  Sutherland's law calculates dynamic viscosity $\mu(T)$:
  $$\mu = \mu_0 \left( \frac{T}{T_0} \right)^{3/2} \frac{T_0 + S}{T + S}$$
  $$\frac{Re}{m} = \frac{\rho_\infty u_\infty}{\mu_\infty}$$

#### 2.1.2 Tunnel Operating & Starting Pressure Requirements
In an intermittent blow-down wind tunnel, starting the tunnel requires blowing the initial normal shock through the test section and into the diffuser. Once established, steady supersonic flow can be maintained down to an unchoking/breakdown limit.

- **Normal Shock Total Pressure Ratio ($P_{02} / P_{01}$):**
  $$\frac{P_{02}}{P_{01}} = \left[ \frac{(\gamma + 1) M^2}{(\gamma - 1)M^2 + 2} \right]^{\frac{\gamma}{\gamma - 1}} \left[ \frac{\gamma + 1}{2\gamma M^2 - (\gamma - 1)} \right]^{\frac{1}{\gamma - 1}}$$
- **Starting Stagnation Pressure ($P_{0,start}$):**
  $$P_{0,start} = \frac{P_{back}}{(P_{02} / P_{01})} \times K_{start}$$
  where $K_{start} \approx 1.15 - 1.35$ accounts for boundary-layer blockage and starting shock hysteresis.
- **Minimum Running Stagnation Pressure ($P_{0,run}$):**
  $$P_{0,run} = \frac{P_{back}}{(P_{02} / P_{01}) \times \eta_D}$$
  where $\eta_D$ is the diffuser pressure recovery efficiency.

#### 2.1.3 Storage Tank Pressure Decay & Runtime Modeling
For a storage reservoir of volume $V$ discharging through choked area $A^*$, the rate of mass depletion is:
$$\frac{dm}{dt} = -\dot{m}(t)$$

1. **Adiabatic (Isentropic) Expansion:**
   For rapid blow-downs where heat transfer from the tank walls is negligible, the gas expands isentropically in the tank ($T_0 / T_{0,i} = (P_0 / P_{0,i})^{(\gamma-1)/\gamma}$).
   Integration of the mass conservation equation yields the closed-form analytical decay:
   $$P_0(t) = P_{0,i} \left[ 1 + \left( \frac{\gamma - 1}{2} \right) \tau t \right]^{-\frac{2\gamma}{\gamma - 1}}$$
   $$T_0(t) = T_{0,i} \left[ 1 + \left( \frac{\gamma - 1}{2} \right) \tau t \right]^{-2}$$
   where the characteristic discharge frequency $\tau$ is:
   $$\tau = \frac{\dot{m}_i}{m_i} = \frac{A^* \sqrt{\gamma R T_{0,i}}}{V} \left( \frac{2}{\gamma + 1} \right)^{\frac{\gamma + 1}{2(\gamma - 1)}}$$
   The adiabatic runtime until $P_0(t) = P_{0,cutoff}$ is:
   $$t_{run, adia} = \frac{2}{(\gamma - 1) \tau} \left[ \left( \frac{P_{0,i}}{P_{0,cutoff}} \right)^{\frac{\gamma - 1}{2\gamma}} - 1 \right]$$

2. **Isothermal Discharge:**
   If a thermal storage matrix or pebble-bed heater maintains $T_0(t) = T_{0,i} = \text{const}$:
   $$P_0(t) = P_{0,i} e^{-\tau t}$$
   $$t_{run, iso} = \frac{1}{\tau} \ln\left( \frac{P_{0,i}}{P_{0,cutoff}} \right)$$

3. **Regulated Pressure Blow-Down:**
   With an automatic pressure reducing valve regulating settling chamber pressure to constant $P_{0,req} = P_{0,start}$:
   $$t_{run, reg} = \frac{m_i - m(P_{0,req})}{\dot{m}(P_{0,req})}$$

---

### 2.2 Hypersonic Shock Tube

#### 2.2.1 Fundamental Diaphragm Pressure Ratio Equation
A classic shock tube consists of a high-pressure driver section (State 4) and a low-pressure driven section (State 1) separated by a diaphragm at $x = 0$. Upon rupture, an incident shock wave propagates into the driven gas at Mach number $M_s$, while an unsteady expansion fan propagates back into the driver gas.

The fundamental shock tube relation matching pressures and flow velocities across the contact surface ($P_2 = P_3$, $u_2 = u_3$) is:

$$\frac{P_4}{P_1} = \left[ \frac{2\gamma_1 M_s^2 - (\gamma_1 - 1)}{\gamma_1 + 1} \right] \left[ 1 - \frac{\gamma_4 - 1}{\gamma_1 + 1} \left( \frac{a_1}{a_4} \right) \left( M_s - \frac{1}{M_s} \right) \right]^{-\frac{2\gamma_4}{\gamma_4 - 1}}$$

where:
- $a_1 = \sqrt{\gamma_1 R_1 T_1}$ (speed of sound in driven gas)
- $a_4 = \sqrt{\gamma_4 R_4 T_4}$ (speed of sound in driver gas)

**Theoretical Shock Mach Limit ($M_{s,limit}$):**  
In order for the bracketed term to be positive:
$$M_s - \frac{1}{M_s} < \left( \frac{\gamma_1 + 1}{\gamma_4 - 1} \right) \left( \frac{a_4}{a_1} \right)$$
This defines the maximum achievable shock Mach number as $P_4/P_1 \to \infty$. To attain hypersonic shock speeds ($M_s \ge 5$), the driver sound speed $a_4$ must be maximized by:
1. Using low molecular weight gases (Helium $M_w = 4$ or Hydrogen $M_w = 2$).
2. Preheating the driver gas ($T_4 > 300\text{ K}$).

#### 2.2.2 Intermediate Thermodynamic States

- **State 2 (Behind Incident Shock):**
  $$P_2 = P_1 \left[ 1 + \frac{2\gamma_1}{\gamma_1 + 1} (M_s^2 - 1) \right]$$
  $$T_2 = T_1 \left( \frac{P_2}{P_1} \right) \left[ \frac{\frac{\gamma_1 + 1}{\gamma_1 - 1} + \frac{P_2}{P_1}}{1 + \frac{\gamma_1 + 1}{\gamma_1 - 1} \frac{P_2}{P_1}} \right]^{-1}$$
  $$u_2 = \frac{2 a_1}{\gamma_1 + 1} \left( M_s - \frac{1}{M_s} \right), \quad \rho_2 = \frac{P_2}{R_1 T_2}$$

- **State 3 (Expanded Driver Gas Behind Contact Surface):**
  $$P_3 = P_2, \quad u_3 = u_2$$
  $$T_3 = T_4 \left( \frac{P_3}{P_4} \right)^{\frac{\gamma_4 - 1}{\gamma_4}}, \quad \rho_3 = \frac{P_3}{R_4 T_3}, \quad a_3 = \sqrt{\gamma_4 R_4 T_3}$$

- **State 5 (Reflected Shock Region at End Wall):**
  At the closed end wall ($x = L_1$), the incident shock reflects to bring the flow to rest ($u_5 = 0$):
  $$\frac{P_5}{P_2} = \frac{\frac{\gamma_1 + 1}{\gamma_1 - 1} + 2 - \frac{P_1}{P_2}}{1 + \frac{\gamma_1 + 1}{\gamma_1 - 1} \frac{P_1}{P_2}}$$
  $$\frac{T_5}{T_2} = \frac{P_5}{P_2} \left[ \frac{\frac{\gamma_1 + 1}{\gamma_1 - 1} + \frac{P_5}{P_2}}{1 + \frac{\gamma_1 + 1}{\gamma_1 - 1}\frac{P_5}{P_2}} \right]$$
  Reflected shock speed moving upstream:
  $$W_R = \frac{u_2}{\frac{\rho_5}{\rho_2} - 1}$$

#### 2.2.3 Wave Kinematics, Sizing & Usable Testing Window
At a test position $x_{ts}$ (or end-wall $L_1$):
1. **Incident Shock Arrival:** $t_{shock} = x_{ts} / W_s$, where $W_s = M_s a_1$.
2. **Contact Surface Arrival:** $t_{cs} = x_{ts} / u_2$.
3. **Reflected Expansion Arrival:** The expansion head reflects off the driver end wall at $t = L_4 / a_4$, propagates rightward through the expansion fan, and reaches the test station at $t_{exp}$.

The usable testing window duration $\Delta t_{test}$ is:
$$\Delta t_{test} = \min(t_{cs}, t_{exp}) - t_{shock}$$

To maximize test time, the driver length $L_4$ is sized such that the expansion wave does not truncate the test before the contact surface arrives ($t_{exp} \ge t_{cs}$).

---

## 3. 4-Day Execution Plan & Implementation Log

| Day | Milestone | Implementation & Code Deliverables | Status |
| :--- | :--- | :--- | :---: |
| **Day 1** | **Gas Dynamics & Shock Relations** | Built `core/gas_dynamics.py` with 1D isentropic relations, Area-Mach inversion, normal shock formulas, Sutherland viscosity, and multi-gas database (`Air`, `He`, `N2`, `CO2`, `Ar`, `H2`). | **Complete** |
| **Day 2** | **Blow-Down Decay & Wave Solver** | Built `core/supersonic_tunnel.py` (nozzle throat sizing, choked mass flow, starting/running pressure limits, adiabatic/isothermal/regulated decay) and `core/shock_tube.py` (diaphragm $P_4/P_1$, states 1-5, wave tracking, testing window). | **Complete** |
| **Day 3** | **Interactive User Interfaces** | Built dual interfaces: (1) `app_gui_tk.py` standalone desktop GUI with embedded Matplotlib canvas, and (2) `app_streamlit.py` modern reactive web app with live plots, sliders, and KPI cards. Built `cli.py` for terminal runs. | **Complete** |
| **Day 4** | **Benchmark Validation & Report** | Created `generate_sample_runs.py`, executed benchmark cases for $M = 2.0, 3.0, 5.0$, generated 5 publication figures, exported CSV datasets, and compiled final engineering report. | **Complete** |

---

## 4. Benchmark Results & Comparative Analysis ($M = 2.0, 3.0, 5.0$)

### 4.1 Supersonic Blow-Down Wind Tunnel Benchmark Results
**Test Conditions:** Test Section Area $A = 0.04\text{ m}^2$ ($20\times 20\text{ cm}$), Reservoir Tank $P_0 = 20\text{ bar}$ ($2.0\text{ MPa}$), Tank Volume $V = 10\text{ m}^3$, $T_0 = 300\text{ K}$, Ambient $P_{back} = 1.013\text{ bar}$.

| Parameter | Symbol / Units | Mach 2.0 | Mach 3.0 | Mach 5.0 | Physical Significance / Trend |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Area Ratio** | $A / A^*$ | **1.6875** | **4.2346** | **25.000** | Non-linear growth with Mach number ($A/A^* \propto M^{\gamma/(\gamma-1)}$) |
| **Throat Area** | $A^*$ ($\text{cm}^2$) | **237.04** | **94.46** | **16.00** | Throat must shrink dramatically for higher Mach numbers |
| **Throat Diameter** | $D^*$ ($\text{cm}$) | **17.37** | **10.97** | **4.51** | Circular equivalent throat dimension |
| **Initial Mass Flow**| $\dot{m}_i$ ($\text{kg/s}$) | **110.62** | **44.08** | **7.47** | Mass flow scales directly with throat area $A^*$ |
| **Static Temperature**| $T_{ts}$ ($\text{K}$) | **166.7** | **107.1** | **50.0** | Extreme isentropic expansion cooling (condensation risk at $M=5$) |
| **Static Pressure** | $P_{ts}$ ($\text{kPa}$) | **255.61** | **54.45** | **3.78** | Vacuum-level test section static pressures at hypersonic speeds |
| **Flow Velocity** | $u_\infty$ ($\text{m/s}$) | **517.6** | **622.5** | **708.8** | Approaches maximum theoretical limit $u_{max} = \sqrt{2 C_p T_0} = 776\text{ m/s}$ |
| **Unit Reynolds No.**| $Re/m$ ($\times 10^6/\text{m}$)| **244.3** | **148.3** | **58.1** | High Reynolds capability typical of blow-down facilities |
| **Starting Pressure**| $P_{0,start}$ ($\text{bar}$)| **1.82** | **3.99** | **21.25** | High Mach starting shock total pressure loss increases steeply |
| **Min. Running Press**| $P_{0,run}$ ($\text{bar}$)| **1.65** | **3.63** | **19.32** | Required pressure to prevent tunnel unchoking |
| **Adiabatic Runtime** | $t_{run}$ ($\text{s}$) | **4.49** | **7.27** | **0.78\*** | Smaller throat reduces mass discharge rate, extending runtime until starting limit exceeds tank supply |
| **Regulated Runtime** | $t_{run,reg}$ ($\text{s}$) | **18.92** | **18.04** | **0.00\*** | Constant $P_0$ throttling provides stable steady-state testing |

*\*Note on Mach 5.0:* Because $P_{0,start} = 21.25\text{ bar}$ exceeds the initial $20\text{ bar}$ tank charge, the tunnel cannot self-start against atmospheric back pressure without either increasing storage tank pressure or employing an evacuated vacuum dump tank (indraft/blow-down hybrid).

---

### 4.2 Hypersonic Shock Tube Benchmark Results
**Test Conditions:** Driver Gas = **Helium ($\text{He}$)**, Driven Gas = **Air**, $P_1 = 10\text{ kPa}$, $T_1 = 300\text{ K}$, $T_4 = 300\text{ K}$, Driver Length $L_4 = 3.0\text{ m}$, Driven Length $L_1 = 9.0\text{ m}$, Test Station $x_{ts} = 9.0\text{ m}$ (End-Wall).

| Parameter | Symbol / Units | $M_s = 2.0$ | $M_s = 3.0$ | $M_s = 5.0$ | Physical Significance / Trend |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Diaphragm Ratio** | $P_4 / P_1$ | **9.68** | **44.25** | **599.65** | Exponential rise with shock Mach number |
| **Driver Pressure** | $P_4$ ($\text{bar}$) | **0.97** | **4.43** | **59.97** | High pressure driver required for hypersonic shock |
| **Incident Shock Speed** | $W_s$ ($\text{m/s}$) | **694.4** | **1041.7** | **1736.1** | Hypervelocity shock wave propagation |
| **Induced Flow Speed**| $u_2$ ($\text{m/s}$) | **434.0** | **771.6** | **1388.9** | High-speed test flow behind incident shock |
| **Post-Shock Temp** | $T_2$ ($\text{K}$) | **506.2** | **803.7** | **1740.0** | Extreme shock heating of driven air |
| **Post-Shock Press** | $P_2$ ($\text{kPa}$) | **45.00** | **103.33** | **290.00** | Strong shock compression |
| **Reflected Temp** | $T_5$ ($\text{K}$) | **750.0** | **1425.9** | **3564.0** | Reservoir conditions for reflected shock tunnel nozzle |
| **Reflected Press** | $P_5$ ($\text{kPa}$) | **150.00** | **516.67** | **1914.00** | Stagnation pressure behind reflected shock ($19.1\text{ bar}$) |
| **Usable Test Time** | $\Delta t_{test}$ ($\text{ms}$)| **2.64** | **3.02** | **1.30** | Millisecond-scale testing window typical of shock tubes |
| **Limiting Factor** | Boundary | **Reflected Expansion**| **Contact Surface** | **Contact Surface** | Boundary determining end of steady test gas |
| **Optimum $L_4/L_1$** | Ratio | **0.649** | **0.175** | **0.024** | Driver length required to prevent expansion cutoff |

---

### 4.3 Analysis & Engineering Insights

1. **Driver Gas Molecular Weight Effect:**
   Using Helium ($M_w = 4\text{ g/mol}$) instead of Nitrogen ($M_w = 28\text{ g/mol}$) increases driver sound speed from $a_4 \approx 353\text{ m/s}$ to $a_4 \approx 1020\text{ m/s}$. For $M_s = 3.0$, a Helium driver requires $P_4/P_1 = 44.25$, whereas a Nitrogen driver would require $P_4/P_1 > 350$. For $M_s = 5.0$, a room-temperature Nitrogen driver cannot physically drive a shock in air because it hits the expansion limit ($M_{s,limit} \approx 3.76$). Preheating or light gases are mandatory for hypersonic testing.

2. **Throat Sizing vs. Blow-Down Runtime:**
   At higher Mach numbers, the throat area $A^*$ shrinks dramatically ($A^* = 237\text{ cm}^2$ at $M=2$ down to $94.5\text{ cm}^2$ at $M=3$). Counterintuitively, this smaller throat restricts mass flow, increasing the unchoke runtime from $4.5\text{ s}$ at $M=2$ to $7.3\text{ s}$ at $M=3$ for the same tank volume, provided the tank pressure is sufficient to start the tunnel.

3. **Shock Tube Usable Testing Window:**
   The testing window is on the order of $1.3 - 3.0\text{ ms}$. At lower Mach numbers ($M_s \approx 2$), the expansion wave travels faster relative to the flow, making reflected expansion wave arrival the limiting factor unless the driver section is sufficiently long ($L_4/L_1 \ge 0.65$). At higher Mach numbers ($M_s \ge 3$), the contact surface travels much faster, becoming the primary boundary that contaminates the test section with driver gas.

---

## 5. Verification & Code Validation

The computational models were verified against established benchmark literature:

1. **Isentropic Relations Validation:**
   At $M = 2.0$, $\gamma = 1.4$:
   - Computed: $T/T_0 = 0.55556$, $P/P_0 = 0.12780$, $A/A^* = 1.6875$.
   - NACA 1135 Table I: $T/T_0 = 0.5556$, $P/P_0 = 0.1278$, $A/A^* = 1.6875$ (Relative Error $< 10^{-6}$).

2. **Normal Shock Validation:**
   At $M_1 = 2.0$, $\gamma = 1.4$:
   - Computed: $M_2 = 0.57735$, $P_2/P_1 = 4.5000$, $T_2/T_1 = 1.6875$, $P_{02}/P_{01} = 0.72087$.
   - NACA 1135 Table II: $M_2 = 0.57735$, $P_2/P_1 = 4.5000$, $P_{02}/P_{01} = 0.7209$ (Relative Error $< 10^{-5}$).

3. **Shock Tube Validation:**
   For $M_s = 3.0$ Helium driving Air:
   - Analytical closed-form solution yields $P_4/P_1 = 44.25$, exactly matching our solver output.

---

## 6. Software Architecture & User Manual

### 6.1 Project Directory Structure
```
Wind Tunnel Technique/
├── core/
│   ├── __init__.py            # Unified package exports
│   ├── gas_dynamics.py        # Isentropic & Normal shock relations, gas database
│   ├── supersonic_tunnel.py   # Blow-down tunnel sizing & runtime decay solver
│   ├── shock_tube.py          # Shock tube relation, states 1-5, wave kinematics
│   └── nozzle_contour.py      # Nozzle aerodynamic geometry & axial M(x/L) solver
├── app_gui_tk.py              # Desktop Native GUI (Tkinter + Matplotlib)
├── app_streamlit.py           # Web Dashboard Application (Streamlit)
├── cli.py                     # Command-Line Interface with interactive & batch modes
├── generate_sample_runs.py    # Batch benchmark generator for M=2, 3, 5
├── tests/
│   └── test_gas_dynamics.py   # Comprehensive physics test suite
├── outputs/
│   ├── plots/                 # Generated publication-quality PNG figures
│   └── data/                  # Exported CSV benchmark tables
├── reports/
│   └── FINAL_PROJECT_REPORT.md# This comprehensive technical project report
└── README.md                  # Quick-start documentation and guide
```

### 6.2 Running the Application

1. **Run Physics Unit Tests:**
   ```bash
   python tests/test_gas_dynamics.py
   ```

2. **Launch Desktop Native GUI (Tkinter):**
   ```bash
   python app_gui_tk.py
   ```

3. **Launch Web Dashboard (Streamlit):**
   ```bash
   python -m streamlit run app_streamlit.py
   ```

4. **Run CLI Quick Calculation:**
   ```bash
   # Supersonic Blow-Down Tunnel:
   python cli.py supersonic --mach 2.5 --area 0.04 --p0 20.0 --volume 10.0

   # Hypersonic Shock Tube:
   python cli.py shocktube --mach 3.0 --driver He --driven Air --p1 10.0
   ```

5. **Regenerate Benchmark Data & Figures:**
   ```bash
   python generate_sample_runs.py
   ```

---

## 7. Conclusion

The developed toolkit successfully unites the theoretical foundations of **Supersonic Wind Tunnel Aerodynamics** and **Hypersonic Shock Tube Dynamics** into a verified, automated software package. By combining 1D compressible isentropic relations, normal shock total pressure loss calculations, unsteady tank discharge ODE integration, and Riemann shock tube wave tracking, the software provides aerospace students and test engineers with an intuitive, highly rigorous platform for high-speed facility design and runtime optimization.
