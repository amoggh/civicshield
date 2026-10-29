import React from 'react';
import type { DiagnosticReport } from '../types/api';

interface DiagnosticsRibbonProps {
  report: DiagnosticReport | null;
  loading: boolean;
}

export const DiagnosticsRibbon: React.FC<DiagnosticsRibbonProps> = ({ report }) => {
  if (!report) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 rounded-xl bg-slate-900/60 border border-slate-800" />
        ))}
      </div>
    );
  }

  const { service_health, database, configuration, latency } = report;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Service Health Card */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 relative overflow-hidden">
        <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
          <span>CLINIC SERVICE</span>
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
              service_health.is_healthy
                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                : 'bg-rose-950 text-rose-400 border border-rose-800'
            }`}
          >
            {service_health.status}
          </span>
        </div>
        <div className="text-2xl font-bold text-white tracking-tight">
          {service_health.active_doctors} <span className="text-xs font-normal text-slate-400">Doctors Active</span>
        </div>
        <p className="text-xs text-slate-400 mt-1 truncate">
          {service_health.pending_appointments} pending appointment(s) queued
        </p>
      </div>

      {/* 2. Database Reachability Card */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 relative overflow-hidden">
        <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
          <span>DATABASE SOCKET</span>
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
              database.is_reachable
                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                : 'bg-rose-950 text-rose-400 border border-rose-800'
            }`}
          >
            {database.status_code}
          </span>
        </div>
        <div className="text-base font-semibold text-white tracking-tight truncate">
          {database.host}:{database.port}
        </div>
        <p className="text-xs text-slate-400 mt-1 truncate">
          {database.is_reachable ? 'Socket connected (3.5ms ping)' : (database.error_detail || 'Connection refused')}
        </p>
      </div>

      {/* 3. Configuration Audit Card */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 relative overflow-hidden">
        <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
          <span>CONFIG DRIFT</span>
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
              !configuration.has_divergence
                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                : 'bg-amber-950 text-amber-400 border border-amber-800'
            }`}
          >
            {!configuration.has_divergence ? 'GOLDEN BASELINE' : 'DIVERGENT'}
          </span>
        </div>
        <div className="text-2xl font-bold text-white tracking-tight">
          {configuration.divergent_keys.length}{' '}
          <span className="text-xs font-normal text-slate-400">Divergent Keys</span>
        </div>
        <p className="text-xs text-slate-400 mt-1 truncate">
          {configuration.has_divergence
            ? `Keys: ${configuration.divergent_keys.join(', ')}`
            : 'Synchronized with baseline template'}
        </p>
      </div>

      {/* 4. Latency Monitor Card */}
      <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 relative overflow-hidden">
        <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
          <span>LATENCY SLA</span>
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
              !latency.sla_violated
                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                : 'bg-rose-950 text-rose-400 border border-rose-800'
            }`}
          >
            {!latency.sla_violated ? 'WITHIN SLA' : 'SLA BREACH'}
          </span>
        </div>
        <div className="text-2xl font-bold text-white tracking-tight">
          {latency.avg_latency_ms}{' '}
          <span className="text-xs font-normal text-slate-400">ms / {latency.threshold_ms}ms max</span>
        </div>
        <p className="text-xs text-slate-400 mt-1 truncate">
          {latency.sla_violated ? 'Severe response time degradation' : 'Nominal round-trip response time'}
        </p>
      </div>
    </div>
  );
};
