import React from 'react';
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
  const getStatusBadge = () => {
    if (!health) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
          <span className="h-2 w-2 rounded-full bg-slate-500 animate-pulse" />
          CONNECTING...
        </span>
      );
    }
    if (health.status === 'healthy') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping opacity-75" />
          <span className="h-2 w-2 rounded-full bg-emerald-500 -ml-3.5" />
          OPERATIONAL (HEALTHY)
        </span>
      );
    }
    if (health.status === 'degraded') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-400 border border-amber-800">
          <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
          SERVICE DEGRADED
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-400 border border-rose-800">
        <span className="h-2 w-2 rounded-full bg-rose-500 animate-pulse" />
        SERVICE DOWN
      </span>
    );
  };

  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center shadow-lg shadow-emerald-500/20 text-white font-black text-xl">
            CS
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white">
                Civic<span className="text-emerald-400">Shield</span>
              </h1>
              <span className="text-xs uppercase tracking-widest px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                v0.6.0
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Safety-Governed Autonomous Incident Response & Verification
            </p>
          </div>
        </div>

        {/* Status Indicators & Refresh */}
        <div className="flex items-center gap-3">
          {getStatusBadge()}

          {agentStatus && (
            <span
              className={`text-xs px-2.5 py-1 rounded-md border font-medium ${
                agentStatus.has_api_key
                  ? 'bg-blue-950/50 text-blue-300 border-blue-800'
                  : 'bg-purple-950/50 text-purple-300 border-purple-800'
              }`}
            >
              {agentStatus.has_api_key ? 'Gemini 2.5 Active' : 'Deterministic Fallback Active'}
            </span>
          )}

          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors border border-slate-700 disabled:opacity-50"
            title="Refresh System Diagnostics"
          >
            <svg
              className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
};
