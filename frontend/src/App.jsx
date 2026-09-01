import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { StationDataProvider } from './context/StationDataContext';
import MainLayout from './components/layout/MainLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import DigitalTwin from './pages/DigitalTwin';
import Weather from './pages/Weather';
import FuelPage from './pages/Fuel';
import PowerPage from './pages/Power';
import Inventory from './pages/Inventory';
import Alerts from './pages/Alerts';
import Prediction from './pages/Prediction';
import Reports from './pages/Reports';
import SettingsPage from './pages/Settings';

export function App() {
  return (
    <StationDataProvider>
      <BrowserRouter>
        <Routes>
          {/* Public / Auth Route */}
          <Route path="/login" element={<Login />} />

          {/* Protected Main SCADA Layout */}
          <Route element={<MainLayout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/digital-twin" element={<DigitalTwin />} />
            <Route path="/weather" element={<Weather />} />
            <Route path="/power" element={<PowerPage />} />
            <Route path="/fuel" element={<FuelPage />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/prediction" element={<Prediction />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>

          {/* Catch-all fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </StationDataProvider>
  );
}

export default App;
