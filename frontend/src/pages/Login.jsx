import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Lock, Compass, KeyRound, Fingerprint, CheckCircle2, AlertCircle } from 'lucide-react';
import { useStationData } from '../context/StationDataContext';

export const Login = () => {
  const navigate = useNavigate();
  const { stationData } = useStationData();
  const [stationKey, setStationKey] = useState('SIH-2026-POLAR-ALPHA');
  const [officerId, setOfficerId] = useState('EXP45-CMD-RAJESHWAR');
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [authSuccess, setAuthSuccess] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();
    setIsAuthenticating(true);
    setTimeout(() => {
      setIsAuthenticating(false);
      setAuthSuccess(true);
      setTimeout(() => {
        navigate('/dashboard');
      }, 700);
    }, 1000);
  };

  return (
    <div className="min-h-screen w-screen bg-[#121212] flex items-center justify-center p-4 scada-grid-bg relative overflow-hidden">
      {/* Background Polar Glow Effect */}
      <div className="absolute w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none -top-20 -left-20" />
      <div className="absolute w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none -bottom-20 -right-20" />

      <div className="w-full max-w-md bg-[#1E1E1E] border border-cyan-500/30 rounded-xl p-6 md:p-8 shadow-2xl relative z-10">
        {/* Top Accent */}
        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-cyan-500 via-blue-500 to-emerald-500 rounded-t-xl" />

        {/* Brand Header */}
        <div className="text-center mb-6">
          <div className="mx-auto w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border border-cyan-500/50 flex items-center justify-center text-cyan-400 mb-3 shadow-scada-glow">
            <Compass className="w-8 h-8 animate-pulse-slow" />
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">ANTARCTIC DIGITAL TWIN</h1>
          <p className="text-xs font-scada-mono text-cyan-400 font-semibold mt-1">
            {stationData?.station?.code || 'SIH26060'} // SCADA MISSION CONTROL
          </p>
          <p className="text-xs text-zinc-400 mt-1">
            {stationData?.station?.name || 'Bharati-Maitri Polar Research Station'}
          </p>
        </div>

        {/* Security Notice */}
        <div className="mb-6 p-3 rounded-lg bg-[#141414] border border-[#2A2A2A] flex items-start gap-2.5 text-xs text-zinc-300">
          <Shield className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
          <span>
            Secure Polar Subsystem Gateway. Session is protected by Madrid Protocol Data Encryption & Offline Satellite Cache.
          </span>
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-scada-mono font-semibold uppercase text-zinc-400 mb-1.5">
              Mission Officer ID
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
                ACCESS GRANTED - ENTERING MISSION CONTROL...
              </>
            ) : (
              <>
                <Fingerprint className="w-4 h-4" />
                INITIALIZE SCADA SESSION
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
