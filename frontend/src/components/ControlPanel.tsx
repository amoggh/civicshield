import React, { useState } from 'react';

interface ControlPanelProps {
  activeFaults: string[];
  isInvestigating: boolean;
  onInjectFault: (faultType: string, params: Record<string, unknown>) => void;
  onResetSimulator: () => void;
  onRunInvestigation: (forceFallback: boolean) => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  activeFaults,
  isInvestigating,
  onInjectFault,
  onResetSimulator,
  onRunInvestigation,
}) => {
  const [selectedScenario, setSelectedScenario] = useState<string>('invalid_db_config');
  const [forceFallback, setForceFallback] = useState<boolean>(true);

  const handleInject = () => {
    let params: Record<string, unknown> = {};
    if (selectedScenario === 'invalid_db_config') {
      params = { corrupt_host: 'unreachable-db.internal', corrupt_port: 9999 };
    } else if (selectedScenario === 'high_latency') {
      params = { added_latency_ms: 3000 };
    }
    onInjectFault(selectedScenario, params);
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        {/* Left side: Fault Injection simulation controls */}
        <div className="flex-1 space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Fault Injection Simulator
            </span>
            {activeFaults.length > 0 ? (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800 animate-pulse">
                Active Fault: {activeFaults.join(', ')}
              </span>
            ) : (
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                Baseline Healthy
              </span>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              disabled={isInvestigating}
              className="bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50"
            >
              <option value="invalid_db_config">Scenario 1: Database Config Drift (Host/Port mismatch)</option>
              <option value="db_unavailable">Scenario 2: Database Server Outage (Socket refused)</option>
              <option value="high_latency">Scenario 3: Latency Overhead (+3000ms SLA breach)</option>
            </select>

            <button
              onClick={handleInject}
              disabled={isInvestigating}
              className="px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-medium text-sm transition-colors shadow-lg shadow-amber-600/20 disabled:opacity-50"
            >
              Inject Fault
            </button>

            <button
              onClick={onResetSimulator}
              disabled={isInvestigating}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm transition-colors border border-slate-700 disabled:opacity-50"
            >
              Reset to Baseline
            </button>
          </div>
        </div>

        {/* Right side: Autonomous Workflow Runner */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 lg:border-l lg:border-slate-800 lg:pl-6">
          <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300 select-none">
            <input
              type="checkbox"
              checked={forceFallback}
              onChange={(e) => setForceFallback(e.target.checked)}
              className="rounded bg-slate-950 border-slate-700 text-emerald-500 focus:ring-emerald-500 h-4 w-4"
            />
            <span>Deterministic Fallback Mode</span>
          </label>

          <button
            onClick={() => onRunInvestigation(forceFallback)}
            disabled={isInvestigating}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-bold text-sm tracking-wide shadow-lg shadow-emerald-500/25 transition-all transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isInvestigating ? (
              <>
                <svg className="animate-spin h-4 w-4 text-slate-950" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Orchestrating Graph...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4 text-slate-950" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                </svg>
                <span>Run Investigation</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

