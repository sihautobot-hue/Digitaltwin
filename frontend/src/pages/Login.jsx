import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Lock, Compass, KeyRound, Fingerprint, CheckCircle2, AlertCircle, ShieldCheck, Radio } from 'lucide-react';
import { useStationData } from '../context/StationDataContext';

export const Login = () => {
  const navigate = useNavigate();
  const { data, switchUser, setUserRole, logAuditEvent, setActiveStation } = useStationData();

  const [selectedUserPreset, setSelectedUserPreset] = useState('USR-001'); // Default: Ajit Yadav (Edge)
  const [stationKey, setStationKey] = useState('SIH-2026-POLAR-ALPHA');
  const [officerId, setOfficerId] = useState('EXP45-CMD-AJIT-YADAV');
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [authSuccess, setAuthSuccess] = useState(false);

  const users = data.users || [];

  const handleSelectPreset = (presetUser) => {
    setSelectedUserPreset(presetUser.id);
    setOfficerId(`EXP45-${presetUser.id}-${presetUser.name.replace(/\s+/g, '-').toUpperCase()}`);
  };

  const handleLogin = (e) => {
    e.preventDefault();
    setIsAuthenticating(true);

    const userObj = users.find(u => u.id === selectedUserPreset) || users[0];

    setTimeout(() => {
      setIsAuthenticating(false);
      setAuthSuccess(true);

      // Set user and role in global context
      if (userObj) {
        switchUser(userObj.id);
        if (userObj.activeStation) {
          setActiveStation(userObj.activeStation);
        }
      }

      logAuditEvent(
        'LOGIN_SUCCESS',
        `User ${userObj.name} signed in successfully with role [${userObj.role}].`,
        'INFO'
      );

      setTimeout(() => {
        if (userObj.role === 'SYSTEM_ADMIN') {
          navigate('/admin');
        } else {
          navigate('/dashboard');
        }
      }, 700);
    }, 1000);
  };

  return (
    <div className="min-h-screen w-screen bg-[#121212] flex items-center justify-center p-4 scada-grid-bg relative overflow-hidden">
      {/* Background Polar Glow Effect */}
      <div className="absolute w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none -top-20 -left-20" />
      <div className="absolute w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none -bottom-20 -right-20" />

      <div className="w-full max-w-lg bg-[#1E1E1E] border border-cyan-500/30 rounded-xl p-6 md:p-8 shadow-2xl relative z-10">
        {/* Top Accent */}
        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-cyan-500 via-blue-500 to-emerald-500 rounded-t-xl" />

        {/* Brand Header */}
        <div className="text-center mb-6">
          <div className="mx-auto w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border border-cyan-500/50 flex items-center justify-center text-cyan-400 mb-3 shadow-scada-glow">
            <Compass className="w-8 h-8 animate-pulse-slow" />
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">ANTARCTIC DIGITAL TWIN</h1>
          <p className="text-xs font-scada-mono text-cyan-400 font-semibold mt-1">
            SIH26060 // SCADA MISSION CONTROL & DIGITAL TWIN
          </p>
          <p className="text-xs text-zinc-400 mt-1">
            Bharati & Maitri Polar Research Stations // NCPOR - MoES
          </p>
        </div>

        {/* Quick RBAC Role Selection Presets */}
        <div className="mb-5 space-y-2">
          <label className="block text-[11px] font-scada-mono font-semibold uppercase text-zinc-400">
            Select Role Profile Preset (RBAC Demonstration)
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {/* Edge Preset */}
            <button
              type="button"
              onClick={() => handleSelectPreset(users[0] || { id: 'USR-001', name: 'Ajit Yadav' })}
              className={`p-2 rounded-lg border text-left transition flex flex-col justify-between ${
                selectedUserPreset === 'USR-001'
                  ? 'bg-emerald-500/15 border-emerald-500 text-white'
                  : 'bg-[#161616] border-[#2A2A2A] text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <div className="text-[10px] font-scada-mono font-bold text-emerald-400 flex items-center gap-1">
                <Shield className="w-3 h-3" /> EDGE COMMANDER
              </div>
              <div className="text-xs font-semibold mt-1 text-zinc-200">Ajit Yadav</div>
              <div className="text-[9px] text-zinc-500 mt-0.5">Real-time / Alert ACK</div>
            </button>

            {/* India Command Preset */}
            <button
              type="button"
              onClick={() => handleSelectPreset(users[2] || { id: 'USR-003', name: 'Dr. Ananya Rao' })}
              className={`p-2 rounded-lg border text-left transition flex flex-col justify-between ${
                selectedUserPreset === 'USR-003'
                  ? 'bg-blue-500/15 border-blue-500 text-white'
                  : 'bg-[#161616] border-[#2A2A2A] text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <div className="text-[10px] font-scada-mono font-bold text-blue-400 flex items-center gap-1">
                <Radio className="w-3 h-3" /> INDIA HQ
              </div>
              <div className="text-xs font-semibold mt-1 text-zinc-200">Dr. Ananya Rao</div>
              <div className="text-[9px] text-zinc-500 mt-0.5">Delayed 12m Mirror</div>
            </button>

            {/* Admin Preset */}
            <button
              type="button"
              onClick={() => handleSelectPreset(users[4] || { id: 'USR-005', name: 'SysAdmin Cyber' })}
              className={`p-2 rounded-lg border text-left transition flex flex-col justify-between ${
                selectedUserPreset === 'USR-005'
                  ? 'bg-purple-500/15 border-purple-500 text-white'
                  : 'bg-[#161616] border-[#2A2A2A] text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <div className="text-[10px] font-scada-mono font-bold text-purple-400 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" /> SYSTEM ADMIN
              </div>
              <div className="text-xs font-semibold mt-1 text-zinc-200">SysAdmin Cell</div>
              <div className="text-[9px] text-zinc-500 mt-0.5">Full /admin Console</div>
            </button>
          </div>
        </div>

        {/* Security Notice */}
        <div className="mb-5 p-3 rounded-lg bg-[#141414] border border-[#2A2A2A] flex items-start gap-2.5 text-xs text-zinc-300">
          <Shield className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
          <span>
            Session is protected by Madrid Protocol Data Encryption & Offline Satellite Cache.
          </span>
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-scada-mono font-semibold uppercase text-zinc-400 mb-1.5">
              Mission Officer ID / Callsign
            </label>
            <div className="relative">
              <KeyRound className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                required
                value={officerId}
                onChange={e => setOfficerId(e.target.value)}
                className="w-full bg-[#141414] border border-[#2A2A2A] focus:border-cyan-500 rounded-lg pl-9 pr-3 py-2 text-xs font-scada-mono text-zinc-200 outline-none transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-scada-mono font-semibold uppercase text-zinc-400 mb-1.5">
              Polar Station Security Token
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={stationKey}
                onChange={e => setStationKey(e.target.value)}
                className="w-full bg-[#141414] border border-[#2A2A2A] focus:border-cyan-500 rounded-lg pl-9 pr-3 py-2 text-xs font-scada-mono text-zinc-200 outline-none transition"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isAuthenticating || authSuccess}
            className={`w-full py-2.5 rounded-lg text-xs font-scada-mono font-bold tracking-wider uppercase transition-all flex items-center justify-center gap-2 ${
              authSuccess
                ? 'bg-green-600 text-white'
                : 'bg-cyan-500 hover:bg-cyan-400 text-black shadow-scada-glow'
            }`}
          >
            {isAuthenticating ? (
              <>
                <Fingerprint className="w-4 h-4 animate-spin" />
                VERIFYING BIOMETRICS & SATELLITE HANDSHAKE...
              </>
            ) : authSuccess ? (
              <>
                <CheckCircle2 className="w-4 h-4" />
                ACCESS GRANTED - INITIALIZING MISSION CONTROL...
              </>
            ) : (
              <>
                <Fingerprint className="w-4 h-4" />
                AUTHENTICATE SCADA SESSION
              </>
            )}
          </button>
        </form>

        {/* Footer info */}
        <div className="mt-6 text-center text-[10px] font-scada-mono text-zinc-500">
          NATIONAL CENTRE FOR POLAR AND OCEAN RESEARCH (NCPOR) / MoES
        </div>
      </div>
    </div>
  );
};

export default Login;
