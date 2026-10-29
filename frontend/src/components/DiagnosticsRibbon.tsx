import React from 'react';
import { Activity, Clock, Database, SlidersHorizontal } from 'lucide-react';
import type { DiagnosticReport } from '../types/api';

interface DiagnosticsRibbonProps {
  report: DiagnosticReport | null;
  loading: boolean;
}

export const DiagnosticsRibbon: React.FC<DiagnosticsRibbonProps> = ({ report }) => {
  if (!report) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 rounded-xl bg-zinc-900/40 border border-zinc-800" />
        ))}
      </div>
    );
  }

  const { service_health, database, configuration, latency } = report;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
      {/* 1. Service Health */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 transition-colors hover:border-zinc-700/80">
        <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
          <span className="flex items-center gap-1.5 font-medium">
            <Activity className="h-3.5 w-3.5 text-zinc-400" />
            Clinic Service
          </span>
          <span
            className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${
              service_health.is_healthy
                ? 'bg-emerald-950/50 text-emerald-400 border-emerald-800/60'
                : 'bg-red-950/50 text-red-400 border-red-800/60'
            }`}
          >
            {service_health.status.toUpperCase()}
          </span>
        </div>
        <div className="text-xl font-semibold text-zinc-100 tracking-tight">
          {service_health.active_doctors}{' '}
          <span className="text-xs font-normal text-zinc-400">Doctors Online</span>
        </div>
        <p className="text-xs text-zinc-400 mt-1 truncate">
          {service_health.pending_appointments} pending appointment(s)
        </p>
      </div>

      {/* 2. Latency Monitor */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 transition-colors hover:border-zinc-700/80">
        <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
          <span className="flex items-center gap-1.5 font-medium">
            <Clock className="h-3.5 w-3.5 text-zinc-400" />
            API Latency
          </span>
          <span
            className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${
              latency.sla_violated
                ? 'bg-red-950/50 text-red-400 border-red-800/60'
                : 'bg-emerald-950/50 text-emerald-400 border-emerald-800/60'
            }`}
          >
            {latency.sla_violated ? 'SLA BREACH' : 'NORMAL'}
          </span>
        </div>
        <div className="text-xl font-semibold text-zinc-100 tracking-tight">
          {latency.avg_latency_ms.toFixed(1)}{' '}
          <span className="text-xs font-normal text-zinc-400">ms roundtrip</span>
        </div>
        <p className="text-xs text-zinc-400 mt-1 truncate">
          {latency.sla_violated
            ? `Exceeded ${latency.threshold_ms}ms SLA limit`
            : `Within ${latency.threshold_ms}ms SLA threshold`}
        </p>
      </div>

      {/* 3. Database Connection */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 transition-colors hover:border-zinc-700/80">
        <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
          <span className="flex items-center gap-1.5 font-medium">
            <Database className="h-3.5 w-3.5 text-zinc-400" />
            Database Socket
          </span>
          <span
            className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${
              database.is_reachable
                ? 'bg-emerald-950/50 text-emerald-400 border-emerald-800/60'
                : 'bg-red-950/50 text-red-400 border-red-800/60'
            }`}
          >
            {database.status_code}
          </span>
        </div>
        <div className="text-xl font-semibold text-zinc-100 tracking-tight truncate">
          {database.is_reachable ? 'Connected' : 'Unavailable'}
        </div>
        <p className="text-xs text-zinc-400 mt-1 truncate">
          {database.is_reachable
            ? `${database.host}:${database.port} (${database.response_time_ms.toFixed(1)}ms)`
            : database.error_detail || 'Connection refused'}
        </p>
      </div>

      {/* 4. Configuration State */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 transition-colors hover:border-zinc-700/80">
        <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
          <span className="flex items-center gap-1.5 font-medium">
            <SlidersHorizontal className="h-3.5 w-3.5 text-zinc-400" />
            Configuration
          </span>
          <span
            className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${
              !configuration.has_divergence
                ? 'bg-emerald-950/50 text-emerald-400 border-emerald-800/60'
                : 'bg-red-950/50 text-red-400 border-red-800/60'
            }`}
          >
            {!configuration.has_divergence ? 'SYNCED' : 'DRIFT DETECTED'}
          </span>
        </div>
        <div className="text-xl font-semibold text-zinc-100 tracking-tight">
          {!configuration.has_divergence ? (
            'Baseline'
          ) : (
            <span className="text-red-400">{configuration.divergent_keys.length} Field(s) Altered</span>
          )}
        </div>
        <p className="text-xs text-zinc-400 mt-1 truncate font-mono">
          {!configuration.has_divergence
            ? 'port: 5432 · pool: 20'
            : configuration.diffs
                .map((d) => `${d.key}: ${String(d.current_value)}`)
                .join(', ')}
        </p>
      </div>
    </div>
  );
};
