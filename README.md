# ❄️ Antarctic Digital Twin (SIH26060)

[![React](https://img.shields.io/badge/Frontend-React_18_%2B_Vite-61DAFB?logo=react&logoColor=black)](frontend/)
[![Spring Boot](https://img.shields.io/badge/Backend-Spring_Boot_3-6DB33F?logo=springboot&logoColor=white)](digitaltwin/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS-38B2AC?logo=tailwind-css&logoColor=white)](frontend/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An industrial, SCADA-inspired government mission control dashboard and physical **2D/2.5D Digital Twin** for Antarctic scientific research bases (Maitri & Bharati Stations, NCPOR / Ministry of Earth Sciences, Govt. of India).

---

## 📁 Repository Structure

```
Digitaltwin/
├── digitaltwin/      # Spring Boot Backend API (Controllers, Services, Repositories, Models)
├── frontend/         # React 18 + Vite + Tailwind SCADA Mission Control Dashboard
└── README.md         # Monorepo Project Overview
```

---

## 🚀 Modules Overview

### 🖥️ Frontend (`/frontend`)
- **Interactive 2D Station Digital Twin**: High-fidelity isometric visual model mapping physical station modules (Powerhouse, Habitat, Cryo Fuel Farm, Comms Radome, Water Pump, Storage Depot, Vehicle Workshop).
- **SCADA Mission Control Suite**:
  - Live Atmosphere & Katabatic Wind Observatory (360° radar compass & blizzard warning alerts).
  - Microgrid Power Switchboard (3x diesel gensets, solar array, micro-wind, 600kWh BESS).
  - Cryogenic Fuel Farm (Tanks A–D, transfer pumps, 225-day winter autonomy buffer).
  - Madrid Protocol Logistics & Spare Parts Registry (Searchable catalog, air-drop manifests).
  - Real-time Alarm Console with AI Root-Cause Inference & Operator Signatures.
  - 72-hour PINN Neural Weather & Demand Forecast Visualizer.
  - Printable Daily Situation Report (SITREP) with PDF & CSV export.
- **Offline-First**: Zero hardcoding, simulated real-time telemetry ticks, and local storage caching.

### ⚙️ Backend (`/digitaltwin`)
- **Spring Boot 3 REST API**: Handles telemetry data persistence, sync status, alert services, fuel, power, inventory, and weather endpoints.
- Maven-based build (`pom.xml` / `mvnw`).

---

## ⚡ Quick Start

### 1. Running the Frontend
```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:3000/`.

### 2. Running the Backend
```bash
cd digitaltwin
./mvnw spring-boot:run
```
Backend API will be accessible on `http://localhost:8080/`.

---

## 🛡️ License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
