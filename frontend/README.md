# ❄️ Antarctic Digital Twin (SIH26060) – SCADA Mission Control Dashboard

[![React](https://img.shields.io/badge/React-18.3.1-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Recharts](https://img.shields.io/badge/Recharts-2.15-22c55e)](https://recharts.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An ultra-modern, SCADA-inspired government mission control dashboard and **2D/2.5D Physical Digital Twin** for Antarctic scientific research bases (Maitri & Bharati Stations, National Centre for Polar and Ocean Research - NCPOR / Ministry of Earth Sciences, Govt. of India).

Designed with a strict dark-mode SCADA aesthetic (`#121212` background, `#1E1E1E` panels, `#2A2A2A` borders), monospace telemetry readouts (**JetBrains Mono**), dynamic status indicators, physics-informed neural network (PINN) forecasts, and **100% offline-first capability**.

---

## 🚀 Key Features

### 🏢 1. Interactive 2D Station Digital Twin
- **Isometric Visual Model**: High-fidelity visual layout of the Antarctic research station on snowy terrain.
- **Physical Modules Mapped**:
  - ⚡ **Power House**: Solar arrays, vertical wind turbines, and diesel gensets.
  - 🏠 **Main Habitat Core**: Living quarters, galley, telemedicine bay with Indian Tricolour flag mast.
  - ⛽ **Fuel Farm**: Cryogenic double-walled polar diesel and Jet-A1 tanks.
  - 📡 **Comms Unit**: High-gain satellite dish and radome tracking GSAT-7A.
  - 💧 **Water Pump House**: Heated lake intake lines drawing from Lake Priyadarshini.
  - 📦 **Storage / Logistics**: Cargo container staging depot and parts vault.
  - 🔧 **Workshop**: PistenBully tracked vehicle and snowmobile maintenance bay.
- **Animated SVG Pipeline Infrastructure**: Umbilical lines connecting facilities with pulsing junction nodes.
- **Interactive Controls**: Toggle label badges, switch view modes, and click on any facility to open its real-time subsystem telemetry inspection modal.

### 📊 2. Zero-Hardcoded & Offline-First Telemetry Engine
- **Centralized Data Store (`dummyData.json`)**: Every metric, sensor value, generator status, alarm, and inventory item is driven by a single structured data schema.
- **Real-Time Simulation (`StationDataContext.jsx`)**: Realistic micro-fluctuations (sensor jitter) in temperature, Katabatic winds, bus frequency, and satellite latency.
- **Offline Persistence**: Full state caching in browser `localStorage` ensuring continuous operation without external internet connection.

### ⚡ 3. Microgrid & Power Switchboard
- Triple-redundant Genset telemetry: CAT 3406 Arctic Diesel, Cummins QSM11, and Kirloskar Emergency Generator.
- Real-time controls: `START`, `STANDBY`, and `SHUTDOWN` generator triggers.
- Micro-wind turbine and solar PV contribution monitoring.
- BESS 600kWh Lithium Iron Phosphate battery state of charge (SoC) and cycle health.
- Emergency load-shedding circuit breaker control matrix (L1 Life Support, L1 Comms, L2 Lab, L3 Helipad).

### ⛽ 4. Cryogenic Fuel Farm Management
- 4 double-walled vacuum-insulated cryogenic tanks (Tanks A–D) with liquid fill animations.
- Autonomous transfer pumps with interactive `START` / `STOP` toggling.
- 225.5-day winter survival autonomy buffer calculation against Madrid Protocol targets.
- Trace heating status and 12-zone hydrocarbon leak detection matrix.

### 🌪️ 5. Polar Meteorology & Katabatic Wind Observatory
- 360° Katabatic Wind Radar Compass showing live wind vector angle, velocity (knots), and peak gusts.
- Severe Blizzard Warning alarm banner with ETA countdown and protocol advisories.
- Space Weather telemetry: Geomagnetic Kp index (Kp 6.3 - G2 storm) and Aurora probability gauge (92%).
- 7-day polar weather forecast and 24-hour historical barograph.

### 📦 6. Madrid Protocol Logistics & Spares Ledger
- Dynamic searchable, filterable warehouse catalog across 7 categories.
- Real-time quantity adjustment (`+` / `-`) buttons updating stock levels.
- Minimum threshold alert highlights (`🔴 Critical`, `🟡 Warning`, `🟢 Normal`).
- Automated parachute air-drop resupply manifest submission modal.

### 🚨 7. SCADA Alarm Monitor & AI Diagnostics
- Real-time event log with severity filtering (`CRITICAL`, `WARNING`, `NORMAL`).
- AI Root-Cause Inference engine providing confidence probability scores.
- Recommended operator action checklists.
- Interactive `ACKNOWLEDGE` action updating the live alert ticker in the Topbar.

### 🧠 8. AI Neural Forecast Twin (PINN Models)
- 72-Hour continuous Katabatic storm power and fuel demand simulation.
- Monte Carlo fuel exhaustion horizon scenarios.
- Component Remaining Useful Life (RUL) predictive degradation models with vibration FFT harmonic analysis.

### 📄 9. Printable SITREP & PDF/CSV Export
- Standardized NCPOR / MoES Daily Situation Report (SITREP) formatted for PDF printing (`window.print()`).
- Complete crew accountability, power grid summary, fuel autonomy, and digitized officer signature blocks.
- One-click CSV and JSON data export.

### ⚙️ 10. System Configuration & Offline Cache Controller
- Telemetry polling interval slider (1s to 15s).
- Simulated satellite bandwidth throttle (256 Kbps, 512 Kbps, 2 Mbps).
- SCADA audio alarm buzzer toggle.
- Station Emergency Lockdown Protocol (DEFCON-1).
- Offline cache inspector and factory reset trigger.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Framework** | [React 18](https://react.dev/) + [Vite](https://vitejs.dev/) |
| **Routing** | [React Router v6](https://reactrouter.com/) |
| **Styling** | [Tailwind CSS v3](https://tailwindcss.com/) with SCADA Dark Theme |
| **Typography** | [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) (Telemetry) + [Inter](https://fonts.google.com/specimen/Inter) (Headers) |
| **Charts** | [Recharts](https://recharts.org/) (Area, Line, Bar, Donut Pie) |
| **Icons** | [Lucide React](https://lucide.dev/) |
| **State Management** | React Context API + Browser LocalStorage Persistence |

---

## 🚦 Color Coding Standard (SCADA Compliance)

| Status | Tailwind Classes | Indicator |
| :--- | :--- | :--- |
| **Normal / Active / Online** | `text-green-500 bg-green-500/10 border-green-500/20` | 🟢 Pulsing Green LED |
| **Warning / Standby / Delayed** | `text-yellow-500 bg-yellow-500/10 border-yellow-500/20` | 🟡 Amber Indicator |
| **Critical / Offline / Alarm** | `text-red-500 bg-red-500/10 border-red-500/20` | 🔴 Red Alarm Strobe |
| **Telemetry / Info / Standby** | `text-cyan-400 bg-cyan-500/10 border-cyan-500/20` | 🔷 Cyan Data Readout |

---

## 📦 Project Structure

```
antarctic-digital-twin-sih26060/
├── public/
│   └── assets/
│       └── maitri_twin_base.jpg      # Isometric 3D station landscape render
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── DataTable.jsx         # Searchable, sortable, paginated table
│   │   │   ├── MetricCard.jsx        # Monospace telemetry KPI card
│   │   │   ├── SCADAGauge.jsx        # Radial circular meters, tanks & wind compass
│   │   │   └── StatusBadge.jsx       # SCADA color-coded status badge
│   │   ├── digitalTwin/
│   │   │   ├── MaitriStationDigitalTwin.jsx  # Interactive 2D Digital Twin model
│   │   │   ├── ModuleDetailModal.jsx         # Granular subsystem inspection modal
│   │   │   └── Station2DMap.jsx              # Schematic blueprint view
│   │   └── layout/
│   │       ├── MainLayout.jsx        # Layout wrapper
│   │       ├── Sidebar.jsx           # SCADA navigation sidebar
│   │       └── Topbar.jsx            # Clocks, satcom link, live alert ticker
│   ├── context/
│   │   └── StationDataContext.jsx    # Central telemetry state & live simulation
│   ├── data/
│   │   └── dummyData.json            # Central zero-hardcoding polar telemetry schema
│   ├── pages/
│   │   ├── Alerts.jsx                # /alerts (Alarms & AI logs)
│   │   ├── Dashboard.jsx             # /dashboard (Mission Overview)
│   │   ├── DigitalTwin.jsx           # /digital-twin (Station 2D Model)
│   │   ├── Fuel.jsx                  # /fuel (Cryogenic fuel farm)
│   │   ├── Inventory.jsx             # /inventory (Logistics & spares)
│   │   ├── Login.jsx                 # /login (Secure station gateway)
│   │   ├── Power.jsx                 # /power (Microgrid & gensets)
│   │   ├── Prediction.jsx            # /prediction (AI forecast twin)
│   │   ├── Reports.jsx               # /reports (Printable SITREP)
│   │   ├── Settings.jsx              # /settings (Sync & cache controls)
│   │   └── Weather.jsx               # /weather (Katabatic wind & meteorology)
│   ├── App.jsx                       # Router configuration
│   ├── index.css                     # SCADA dark-mode theme & print styles
│   └── main.jsx                      # App entry point
├── index.html
├── package.json
├── tailwind.config.js
└── vite.config.js
```

---

## ⚡ Quick Start

### Prerequisites
- [Node.js](https://nodejs.org/) (v18.0 or higher recommended)
- [npm](https://www.npmjs.com/) (v9.0 or higher)

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/antarctic-digital-twin-sih26060.git
cd antarctic-digital-twin-sih26060
```

### 2. Install dependencies
```bash
npm install
```

### 3. Start development server
```bash
npm run dev
```
Open your browser and navigate to `http://localhost:3000/`.

### 4. Build for production
```bash
npm run build
```

---

## 🛡️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🇮🇳 Acknowledgements
- **Smart India Hackathon (SIH26060)**
- **National Centre for Polar and Ocean Research (NCPOR)**, Ministry of Earth Sciences, Govt. of India
- **Maitri & Bharati Antarctic Research Stations** (Princess Elizabeth Land & Queen Maud Land, Antarctica)
