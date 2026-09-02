import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import initialData from '../data/dummyData.json';

const StationDataContext = createContext(null);

const STORAGE_KEY_DATA = 'ANTARCTIC_SCADA_STATION_DATA_V2';
const STORAGE_KEY_STATION = 'ANTARCTIC_SCADA_ACTIVE_STATION_V2';
const STORAGE_KEY_THEME = 'ANTARCTIC_SCADA_THEME_V2';
const STORAGE_KEY_USER = 'ANTARCTIC_SCADA_CURRENT_USER_V2';

export const StationDataProvider = ({ children }) => {
  // 1. Theme State (default: 'dark')
  const [theme, setTheme] = useState(() => {
    try {
      const savedTheme = localStorage.getItem(STORAGE_KEY_THEME);
      if (savedTheme) return savedTheme;
    } catch (e) {
      console.warn('Could not read theme from localStorage', e);
    }
    return 'dark';
  });

  // Apply dark class to <html> element
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.remove('dark');
      root.classList.add('light');
    }
    try {
      localStorage.setItem(STORAGE_KEY_THEME, theme);
    } catch (e) {
      console.warn('Could not save theme', e);
    }
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  }, []);

  // 2. Active Station State ('maitri' | 'bharati')
  const [activeStation, setActiveStationState] = useState(() => {
    try {
      const savedStation = localStorage.getItem(STORAGE_KEY_STATION);
      if (savedStation && (savedStation === 'maitri' || savedStation === 'bharati')) {
        return savedStation;
      }
    } catch (e) {
      console.warn('Could not read activeStation from localStorage', e);
    }
    return 'maitri';
  });

  // 3. Raw Data Store (Supports stations: { maitri, bharati }, users, auditLogs, settings)
  const [data, setData] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_DATA);
      if (saved) {
        const parsed = JSON.parse(saved);
        // Ensure stations, users, and auditLogs are present
        if (parsed.stations && parsed.users && parsed.auditLogs) {
          return parsed;
        }
      }
    } catch (err) {
      console.warn('Could not load cached SCADA data from localStorage:', err);
    }
    return initialData;
  });

  // 4. Current User & RBAC State
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem(STORAGE_KEY_USER);
      if (savedUser) {
        const parsed = JSON.parse(savedUser);
        const match = data.users?.find(u => u.id === parsed.id);
        if (match) return match;
      }
    } catch (e) {
      console.warn('Could not read currentUser from localStorage', e);
    }
    return data.users?.[0] || {
      id: "USR-001",
      name: "Ajit Yadav",
      role: "ANTARCTICA_EDGE",
      roleLabel: "Antarctica Edge User",
      title: "Station Commander (Expedition 45)",
      location: "Bharati Station Base"
    };
  });

  const [userRole, setUserRoleState] = useState(currentUser.role || 'ANTARCTICA_EDGE');

  // Sync role when user changes
  useEffect(() => {
    if (currentUser?.role) {
      setUserRoleState(currentUser.role);
    }
  }, [currentUser]);

  // Persist current user
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(currentUser));
    } catch (e) {
      console.warn('Could not save currentUser', e);
    }
  }, [currentUser]);

  // Save active station to localStorage
  const setActiveStation = useCallback((stKey) => {
    if (stKey === 'maitri' || stKey === 'bharati') {
      setActiveStationState(stKey);
      try {
        localStorage.setItem(STORAGE_KEY_STATION, stKey);
      } catch (e) {
        console.warn('Could not save activeStation', e);
      }
    }
  }, []);

  // Quick switch role
  const setUserRole = useCallback((newRole) => {
    setUserRoleState(newRole);
    setCurrentUser(prev => ({
      ...prev,
      role: newRole,
      roleLabel: newRole === 'ANTARCTICA_EDGE'
        ? 'Antarctica Edge User'
        : newRole === 'INDIA_COMMAND'
        ? 'India Command Center'
        : 'System Admin'
    }));
  }, []);

  // Switch active user by ID
  const switchUser = useCallback((userId) => {
    const user = data.users?.find(u => u.id === userId);
    if (user) {
      setCurrentUser(user);
      setUserRoleState(user.role);
      if (user.activeStation && (user.activeStation === 'maitri' || user.activeStation === 'bharati')) {
        setActiveStation(user.activeStation);
      }
    }
  }, [data.users, setActiveStation]);

  const [isLiveTelemetryActive, setIsLiveTelemetryActive] = useState(true);
  const [activeAudioAlarm, setActiveAudioAlarm] = useState(false);

  // Persist data state
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_DATA, JSON.stringify(data));
    } catch (err) {
      console.error('Failed to persist SCADA data:', err);
    }
  }, [data]);

  // Active Station Projection: Merges active station telemetry with global users, auditLogs, and settings
  const stationData = useMemo(() => {
    const currentStationTelemetry = data.stations?.[activeStation] || data;
    return {
      ...currentStationTelemetry,
      activeStationKey: activeStation,
      users: data.users || [],
      auditLogs: data.auditLogs || [],
      settings: currentStationTelemetry.settings || data.settings || {}
    };
  }, [data, activeStation]);

  // Check if unacknowledged critical alert exists
  useEffect(() => {
    const alerts = stationData.alerts || [];
    const hasCriticalUnack = alerts.some(
      a => a.severity === 'CRITICAL' && !a.acknowledged
    );
    setActiveAudioAlarm(hasCriticalUnack && (stationData.settings?.audioAlarmsEnabled ?? true));
  }, [stationData.alerts, stationData.settings]);

  // Audit Logging Helper
  const logAuditEvent = useCallback((action, details, severity = 'INFO') => {
    const newLog = {
      id: `AUD-${Date.now().toString().slice(-4)}`,
      timestamp: new Date().toISOString(),
      userId: currentUser.id || 'USR-ANON',
      userName: currentUser.name || 'Anonymous User',
      userRole: userRole,
      action: action,
      ipAddress: currentUser.ipAddress?.split(' - ')[0] || '192.168.1.1',
      location: currentUser.location || (activeStation === 'maitri' ? 'Maitri Station' : 'Bharati Station'),
      details: details,
      severity: severity
    };

    setData(prev => ({
      ...prev,
      auditLogs: [newLog, ...(prev.auditLogs || [])].slice(0, 100)
    }));
  }, [currentUser, userRole, activeStation]);

  // Live Telemetry Simulation Tick for active station
  useEffect(() => {
    if (!isLiveTelemetryActive || !stationData.settings?.dataStreamSimulated) return;

    const intervalMs = (stationData.settings?.pollingIntervalSeconds || 3) * 1000;
    const timer = setInterval(() => {
      setData(prev => {
        const currentSt = prev.stations?.[activeStation] || prev;
        const windDelta = (Math.random() - 0.48) * 1.5;
        const currentWind = currentSt.weather?.current?.windSpeedKnots || 45;
        const newWind = Math.max(20, Math.min(105, +(currentWind + windDelta).toFixed(1)));
        const newGust = +(newWind * 1.35 + Math.random() * 4).toFixed(1);

        const tempDelta = (Math.random() - 0.5) * 0.2;
        const baseOutdoor = currentSt.weather?.current?.outdoorTempC || -40;
        const newOutdoorTemp = +(baseOutdoor + tempDelta).toFixed(1);
        const newWindChill = +(newOutdoorTemp - (newWind * 0.4)).toFixed(1);

        const freqDelta = (Math.random() - 0.5) * 0.02;
        const newFreq = +(50.0 + freqDelta).toFixed(2);
        const voltDelta = (Math.random() - 0.5) * 0.8;
        const newVolt = +(401.5 + voltDelta).toFixed(1);

        const pingJitter = Math.floor((Math.random() - 0.5) * 20);
        const basePing = activeStation === 'bharati' ? 540 : 612;
        const newPing = Math.max(480, Math.min(850, basePing + pingJitter));

        const updatedCurrentSt = {
          ...currentSt,
          station: {
            ...currentSt.station,
            telemetryLink: {
              ...currentSt.station?.telemetryLink,
              latencyMs: newPing,
              lastSyncTimestamp: new Date().toISOString()
            }
          },
          weather: {
            ...currentSt.weather,
            current: {
              ...currentSt.weather?.current,
              outdoorTempC: newOutdoorTemp,
              windChillC: newWindChill,
              windSpeedKnots: newWind,
              windGustKnots: newGust,
              windSpeedKmh: +(newWind * 1.852).toFixed(1)
            }
          },
          power: {
            ...currentSt.power,
            overview: {
              ...currentSt.power?.overview,
              gridFrequencyHz: newFreq,
              busVoltageV: newVolt
            }
          }
        };

        return {
          ...prev,
          stations: {
            ...prev.stations,
            [activeStation]: updatedCurrentSt
          },
          // Also keep root updated if maitri is active
          ...(activeStation === 'maitri' ? updatedCurrentSt : {})
        };
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [isLiveTelemetryActive, activeStation, stationData.settings]);

  // Actions for Active Station
  const acknowledgeAlert = useCallback((alertId, officerName = currentUser.name) => {
    if (userRole === 'INDIA_COMMAND') {
      console.warn('Alert acknowledgement restricted to Antarctica Edge personnel');
      return;
    }

    setData(prev => {
      const currentSt = prev.stations?.[activeStation] || prev;
      const targetAlert = currentSt.alerts?.find(a => a.id === alertId);
      const updatedAlerts = currentSt.alerts?.map(alert => {
        if (alert.id === alertId) {
          return {
            ...alert,
            acknowledged: true,
            acknowledgedBy: officerName,
            acknowledgedAt: new Date().toISOString()
          };
        }
        return alert;
      });

      const updatedSt = {
        ...currentSt,
        alerts: updatedAlerts
      };

      return {
        ...prev,
        stations: {
          ...prev.stations,
          [activeStation]: updatedSt
        },
        ...(activeStation === 'maitri' ? updatedSt : {})
      };
    });

    logAuditEvent('ALERT_ACKNOWLEDGED', `Alert [${alertId}] acknowledged by ${officerName}.`, 'WARNING');
  }, [activeStation, currentUser.name, userRole, logAuditEvent]);

  const toggleStationLockdown = useCallback(() => {
    if (userRole === 'INDIA_COMMAND') {
      console.warn('Lockdown command restricted to Antarctica Edge Commander');
      return;
    }

    let newState = false;
    setData(prev => {
      const currentSt = prev.stations?.[activeStation] || prev;
      newState = !currentSt.station?.lockdownActive;
      const updatedSt = {
        ...currentSt,
        station: {
          ...currentSt.station,
          lockdownActive: newState,
          securityStatus: newState ? 'DEFCON-1 LOCKDOWN' : 'NORMAL'
        }
      };

      return {
        ...prev,
        stations: {
          ...prev.stations,
          [activeStation]: updatedSt
        },
        ...(activeStation === 'maitri' ? updatedSt : {})
      };
    });

    logAuditEvent(
      'LOCKDOWN_TRIGGERED',
      `Emergency lockdown state changed to: ${newState ? 'DEFCON-1 ACTIVE' : 'NORMAL'} for ${activeStation.toUpperCase()}`,
      'SECURITY'
    );
  }, [activeStation, userRole, logAuditEvent]);

  const toggleGenerator = useCallback((genId, targetState) => {
    if (userRole === 'INDIA_COMMAND') return;

    setData(prev => {
      const currentSt = prev.stations?.[activeStation] || prev;
      const updatedSources = currentSt.power?.sources?.map(src => {
        if (src.id === genId) {
          return {
            ...src,
            status: targetState,
            loadKw: targetState === 'NORMAL' ? src.maxKw * 0.65 : 0
          };
        }
        return src;
      });

      const updatedSt = {
        ...currentSt,
        power: {
          ...currentSt.power,
          sources: updatedSources
        }
      };

      return {
        ...prev,
        stations: {
          ...prev.stations,
          [activeStation]: updatedSt
        },
        ...(activeStation === 'maitri' ? updatedSt : {})
      };
    });

    logAuditEvent('DIESEL_GENSET_SWITCH', `Generator ${genId} state changed to ${targetState}`, 'INFO');
  }, [activeStation, userRole, logAuditEvent]);

  const toggleFuelPump = useCallback((pumpId) => {
    if (userRole === 'INDIA_COMMAND') return;

    setData(prev => {
      const currentSt = prev.stations?.[activeStation] || prev;
      const updatedPumps = currentSt.fuel?.pumps?.map(p => {
        if (p.id === pumpId) {
          const nextState = p.status === 'NORMAL' ? 'STANDBY' : 'NORMAL';
          return {
            ...p,
            status: nextState,
            flowRateLpm: nextState === 'NORMAL' ? 45.0 : 0.0
          };
        }
        return p;
      });

      const updatedSt = {
        ...currentSt,
        fuel: {
          ...currentSt.fuel,
          pumps: updatedPumps
        }
      };

      return {
        ...prev,
        stations: {
          ...prev.stations,
          [activeStation]: updatedSt
        },
        ...(activeStation === 'maitri' ? updatedSt : {})
      };
    });

    logAuditEvent('FUEL_PUMP_TOGGLE', `Cryogenic transfer pump ${pumpId} toggled`, 'INFO');
  }, [activeStation, userRole, logAuditEvent]);

  const updateInventoryQuantity = useCallback((itemId, delta) => {
    if (userRole === 'INDIA_COMMAND') return;

    setData(prev => {
      const currentSt = prev.stations?.[activeStation] || prev;
      const updatedItems = currentSt.inventory?.items?.map(item => {
        if (item.id === itemId) {
          const newQty = Math.max(0, item.quantity + delta);
          return {
            ...item,
            quantity: newQty,
            status: newQty <= item.criticalThreshold ? 'CRITICAL' : newQty <= item.minThreshold ? 'WARNING' : 'NORMAL'
          };
        }
        return item;
      });

      const updatedSt = {
        ...currentSt,
        inventory: {
          ...currentSt.inventory,
          items: updatedItems
        }
      };

      return {
        ...prev,
        stations: {
          ...prev.stations,
          [activeStation]: updatedSt
        },
        ...(activeStation === 'maitri' ? updatedSt : {})
      };
    });

    logAuditEvent('INVENTORY_QTY_UPDATE', `Item ${itemId} adjusted by ${delta > 0 ? `+${delta}` : delta}`, 'INFO');
  }, [activeStation, userRole, logAuditEvent]);

  // Admin Operations: User Role Update
  const updateUserRole = useCallback((userId, newRole) => {
    let targetUserName = '';
    setData(prev => {
      const updatedUsers = prev.users?.map(u => {
        if (u.id === userId) {
          targetUserName = u.name;
          return {
            ...u,
            role: newRole,
            roleLabel: newRole === 'ANTARCTICA_EDGE'
              ? 'Antarctica Edge User'
              : newRole === 'INDIA_COMMAND'
              ? 'India Command Center'
              : 'System Admin'
          };
        }
        return u;
      });

      return {
        ...prev,
        users: updatedUsers
      };
    });

    // If updating current user's role
    if (currentUser.id === userId) {
      setUserRoleState(newRole);
      setCurrentUser(prev => ({
        ...prev,
        role: newRole,
        roleLabel: newRole === 'ANTARCTICA_EDGE'
          ? 'Antarctica Edge User'
          : newRole === 'INDIA_COMMAND'
          ? 'India Command Center'
          : 'System Admin'
      }));
    }

    logAuditEvent(
      'ROLE_ASSIGNMENT',
      `Assigned role [${newRole}] to user: ${targetUserName || userId}`,
      'SECURITY'
    );
  }, [currentUser.id, logAuditEvent]);

  // Admin Operations: Update Non-Telemetry System Configs
  const updateSystemConfig = useCallback((key, value) => {
    setData(prev => {
      const currentSt = prev.stations?.[activeStation] || prev;
      const updatedSettings = {
        ...(currentSt.settings || prev.settings || {}),
        [key]: value
      };

      const updatedSt = {
        ...currentSt,
        settings: updatedSettings
      };

      return {
        ...prev,
        settings: updatedSettings,
        stations: {
          ...prev.stations,
          [activeStation]: updatedSt
        }
      };
    });

    logAuditEvent('SYSTEM_CONFIG_UPDATE', `System config [${key}] modified to: ${JSON.stringify(value)}`, 'INFO');
  }, [activeStation, logAuditEvent]);

  // Reset to factory defaults
  const flushOfflineCache = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY_DATA);
      localStorage.removeItem(STORAGE_KEY_STATION);
      localStorage.removeItem(STORAGE_KEY_USER);
    } catch (e) {
      console.warn('Error clearing localStorage', e);
    }
    setData(initialData);
    setActiveStationState('maitri');
    setCurrentUser(initialData.users?.[0] || {
      id: "USR-001",
      name: "Ajit Yadav",
      role: "ANTARCTICA_EDGE"
    });
    setUserRoleState('ANTARCTICA_EDGE');
  }, []);

  // RBAC Permission checks
  const rbac = useMemo(() => ({
    canAcknowledgeAlerts: userRole === 'ANTARCTICA_EDGE' || userRole === 'SYSTEM_ADMIN',
    canEditInventory: userRole === 'ANTARCTICA_EDGE' || userRole === 'SYSTEM_ADMIN',
    canTriggerLockdown: userRole === 'ANTARCTICA_EDGE' || userRole === 'SYSTEM_ADMIN',
    canAccessAdmin: userRole === 'SYSTEM_ADMIN',
    isDelayedFeed: userRole === 'INDIA_COMMAND',
    isEdgeStation: userRole === 'ANTARCTICA_EDGE'
  }), [userRole]);

  return (
    <StationDataContext.Provider
      value={{
        stationData,
        data,
        activeStation,
        setActiveStation,
        theme,
        toggleTheme,
        currentUser,
        userRole,
        setUserRole,
        switchUser,
        updateUserRole,
        updateSystemConfig,
        rbac,
        isLiveTelemetryActive,
        setIsLiveTelemetryActive,
        activeAudioAlarm,
        acknowledgeAlert,
        toggleStationLockdown,
        toggleGenerator,
        toggleFuelPump,
        updateInventoryQuantity,
        logAuditEvent,
        flushOfflineCache
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

export default StationDataContext;
