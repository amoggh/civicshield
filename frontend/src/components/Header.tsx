import React from 'react';
import { ShieldCheck, RefreshCw, Cpu } from 'lucide-react';
import type { ClinicHealthResponse, AgentStatusResponse } from '../types/api';

interface HeaderProps {
  health: ClinicHealthResponse | null;
  agentStatus: AgentStatusResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  agentStatus,
  loading,
  onRefresh,
}) => {
  const isHealthy = health?.status === 'healthy';
  const isDegraded = health?.status === 'degraded';

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Brand & Subtitle */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-zinc-100 flex items-center justify-center text-zinc-950 shadow-sm">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-base text-zinc-100 tracking-tight">
                CivicShield
              </span>
              <span className="text-[11px] font-medium px-1.5 py-0.5 rounded bg-zinc-800/80 text-zinc-400 border border-zinc-700/50">
                v1.0
              </span>
            </div>
            <span className="text-xs text-zinc-500">
              Safety-Governed Autonomous Incident Remediation
            </span>
          </div>
        </div>

        {/* Status Indicators & Action */}
        <div className="flex items-center gap-3">
          {/* Service Status Badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-medium text-zinc-300">
            <span
              className={`h-2 w-2 rounded-full ${
                !health
                  ? 'bg-zinc-500 animate-pulse'
                  : isHealthy
                  ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]'
                  : isDegraded
                  ? 'bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(251,191,36,0.5)]'
                  : 'bg-red-500 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.5)]'
              }`}
            />
            <span>
              {!health
                ? 'Connecting...'
                : isHealthy
                ? 'System Operational'
                : isDegraded
                ? 'Service Degraded'
                : 'Service Outage'}
            </span>
          </div>

          {/* AI Engine Badge */}
          {agentStatus && (
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-zinc-900 border border-zinc-800 text-xs text-zinc-400">
              <Cpu className="h-3.5 w-3.5 text-zinc-400" />
              <span>
                {agentStatus.has_api_key ? 'Gemini 2.5 Active' : 'Deterministic Mode'}
              </span>
            </div>
          )}

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white transition-colors border border-zinc-800 disabled:opacity-50"
            title="Refresh status"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
