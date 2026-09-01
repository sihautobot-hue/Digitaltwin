import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import initialStationData from '../data/dummyData.json';

const StationDataContext = createContext(null);

const STORAGE_KEY = 'ANTARCTIC_SCADA_STATION_DATA_V1';

export const StationDataProvider = ({ children }) => {
  const [data, setData] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (err) {
      console.warn('Could not load cached SCADA data from localStorage:', err);
    }
    return initialStationData;
  });

  const [isLiveTelemetryActive, setIsLiveTelemetryActive] = useState(true);
  const [lastTick, setLastTick] = useState(new Date());
  const [activeAudioAlarm, setActiveAudioAlarm] = useState(false);

  // Save to localStorage when state changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (err) {
      console.error('Failed to persist SCADA data:', err);
    }
  }, [data]);

  // Check if any critical unacknowledged alerts exist to trigger alarm
  useEffect(() => {
    const hasCriticalUnack = data.alerts.some(
      a => a.severity === 'CRITICAL' && !a.acknowledged
    );
    setActiveAudioAlarm(hasCriticalUnack && data.settings.audioAlarmsEnabled);
  }, [data.alerts, data.settings.audioAlarmsEnabled]);

  // Live Telemetry Simulation Tick
  useEffect(() => {
    if (!isLiveTelemetryActive || !data.settings.dataStreamSimulated) return;

    const intervalMs = (data.settings.pollingIntervalSeconds || 3) * 1000;
    const timer = setInterval(() => {
      setData(prev => {
        // Micro fluctuation calculations
        const windDelta = (Math.random() - 0.48) * 1.5;
        const newWind = Math.max(20, Math.min(105, +(prev.weather.current.windSpeedKnots + windDelta).toFixed(1)));
        const newGust = +(newWind * 1.35 + Math.random() * 4).toFixed(1);
        const tempDelta = (Math.random() - 0.5) * 0.2;
        const newOutdoorTemp = +((prev.weather.current.outdoorTempC || -42.8) + tempDelta).toFixed(1);
        const newWindChill = +(newOutdoorTemp - (newWind * 0.4)).toFixed(1);

        // Power micro fluctuation
        const freqDelta = (Math.random() - 0.5) * 0.02;
        const newFreq = +(50.0 + freqDelta).toFixed(2);
        const voltDelta = (Math.random() - 0.5) * 0.8;
        const newVolt = +(401.5 + voltDelta).toFixed(1);

        // Micro wind variation
        const microWindKw = +(Math.min(60, Math.max(10, newWind * 0.75))).toFixed(1);

        // Satellite ping jitter
        const pingJitter = Math.floor((Math.random() - 0.5) * 20);
        const newPing = Math.max(540, Math.min(850, 612 + pingJitter));

        // Fuel burn micro progression (approx 0.05L per tick)
        const burnL = 0.04;
        const activeTank = prev.fuel.tanks.find(t => t.status === 'NORMAL' && t.pumpState === 'ACTIVE') || prev.fuel.tanks[1];

        const updatedTanks = prev.fuel.tanks.map(t => {
          if (t.id === activeTank.id) {
            const nextL = Math.max(5000, +(t.currentLitres - burnL).toFixed(1));
            return {
              ...t,
              currentLitres: nextL,
              percentage: +((nextL / t.capacityLitres) * 100).toFixed(1)
            };
          }
          return t;
        });

        const totalFuelL = updatedTanks.reduce((acc, t) => acc + t.currentLitres, 0);

        return {
          ...prev,
          station: {
            ...prev.station,
            telemetryLink: {
              ...prev.station.telemetryLink,
              latencyMs: newPing,
              lastSyncTimestamp: new Date().toISOString()
            }
          },
          weather: {
            ...prev.weather,
            current: {
              ...prev.weather.current,
              outdoorTempC: newOutdoorTemp,
              windChillC: newWindChill,
              windSpeedKnots: newWind,
              windGustKnots: newGust,
              windSpeedKmh: +(newWind * 1.852).toFixed(1)
            }
          },
          power: {
            ...prev.power,
            overview: {
              ...prev.power.overview,
              gridFrequencyHz: newFreq,
              busVoltageV: newVolt
            },
            sources: prev.power.sources.map(s => {
              if (s.id === 'WIND-ARRAY') {
                return { ...s, loadKw: microWindKw, loadPercent: +((microWindKw / s.maxKw) * 100).toFixed(1) };
              }
              return s;
            })
          },
          fuel: {
            ...prev.fuel,
            summary: {
              ...prev.fuel.summary,
              totalCurrentLitres: totalFuelL,
              overallPercent: +((totalFuelL / prev.fuel.summary.totalCapacityLitres) * 100).toFixed(2)
            },
            tanks: updatedTanks
          }
        };
      });
      setLastTick(new Date());
    }, intervalMs);

    return () => clearInterval(timer);
  }, [isLiveTelemetryActive, data.settings.dataStreamSimulated, data.settings.pollingIntervalSeconds]);

  // Action: Acknowledge an alert
  const acknowledgeAlert = useCallback((alertId, operatorName = 'Cmdr. Operator (SCADA)') => {
    setData(prev => ({
      ...prev,
      alerts: prev.alerts.map(a =>
        a.id === alertId
          ? { ...a, acknowledged: true, acknowledgedBy: operatorName }
          : a
      )
    }));
  }, []);

  // Action: Toggle Generator Active/Standby
  const toggleGenerator = useCallback((genId) => {
    setData(prev => ({
      ...prev,
      power: {
        ...prev.power,
        sources: prev.power.sources.map(s => {
          if (s.id === genId) {
            const isCurrentlyActive = s.status === 'NORMAL' && s.loadKw > 0;
            const newStatus = isCurrentlyActive ? 'STANDBY' : 'NORMAL';
            return {
              ...s,
              status: newStatus,
              loadKw: isCurrentlyActive ? 0 : 85.0,
              loadPercent: isCurrentlyActive ? 0 : 34.0,
              rpm: isCurrentlyActive ? 0 : 1500,
              oilPressureBar: isCurrentlyActive ? 0 : 4.8
            };
          }
          return s;
        })
      }
    }));
  }, []);

  // Action: Toggle Circuit Breaker
  const toggleCircuit = useCallback((circuitId) => {
    setData(prev => ({
      ...prev,
      power: {
        ...prev.power,
        distributionCircuits: prev.power.distributionCircuits.map(c =>
          c.id === circuitId
            ? { ...c, breakerClosed: !c.breakerClosed, currentKw: c.breakerClosed ? 0 : c.capacityKw * 0.7 }
            : c
        )
      }
    }));
  }, []);

  // Action: Toggle Fuel Pump
  const togglePump = useCallback((pumpId) => {
    setData(prev => ({
      ...prev,
      fuel: {
        ...prev.fuel,
        pumps: prev.fuel.pumps.map(p =>
          p.id === pumpId
            ? {
              ...p,
              flowRateLpm: p.flowRateLpm > 0 ? 0.0 : 45.0,
              pressurePsi: p.flowRateLpm > 0 ? 0.0 : 58.0
            }
            : p
        )
      }
    }));
  }, []);

  // Action: Toggle Station Lockdown
  const toggleStationLockdown = useCallback(() => {
    setData(prev => {
      const nextLockdown = !prev.station.lockdownActive;
      return {
        ...prev,
        station: {
          ...prev.station,
          lockdownActive: nextLockdown,
          securityStatus: nextLockdown ? 'CRITICAL' : 'NORMAL'
        }
      };
    });
  }, []);

  // Action: Update Inventory Quantity
  const updateInventoryItem = useCallback((sku, delta) => {
    setData(prev => ({
      ...prev,
      inventory: prev.inventory.map(item => {
        if (item.sku === sku) {
          const newQty = Math.max(0, item.quantity + delta);
          const newStatus = newQty < item.minThreshold
            ? (newQty <= 2 ? 'CRITICAL' : 'WARNING')
            : 'NORMAL';
          return {
            ...item,
            quantity: newQty,
            status: newStatus
          };
        }
        return item;
      })
    }));
  }, []);

  // Action: Update Settings
  const updateSettings = useCallback((newSettings) => {
    setData(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        ...newSettings
      }
    }));
  }, []);

  // Action: Reset Data
  const resetToDefaultData = useCallback(() => {
    setData(initialStationData);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  // Action: Export JSON
  const exportTelemetryJSON = useCallback(() => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(data, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `antarctic-scada-telemetry-${new Date().toISOString().slice(0, 10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  }, [data]);

  return (
    <StationDataContext.Provider
      value={{
        stationData: data,
        isLiveTelemetryActive,
        setIsLiveTelemetryActive,
        lastTick,
        activeAudioAlarm,
        acknowledgeAlert,
        toggleGenerator,
        toggleCircuit,
        togglePump,
        toggleStationLockdown,
        updateInventoryItem,
        updateSettings,
        resetToDefaultData,
        exportTelemetryJSON
      }}
    >
      {children}
    </StationDataContext.Provider>
  );
};

export const useStationData = () => {
  const context = useContext(StationDataContext);
  if (!context) {
    throw new Error('useStationData must be used within a StationDataProvider');
  }
  return context;
};
