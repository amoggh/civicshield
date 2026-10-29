import React, { useState } from 'react';
import { Play, RotateCcw, Zap, AlertTriangle, Loader2 } from 'lucide-react';

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

  const hasFault = activeFaults.length > 0;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
        {/* Left Side: Fault Injection */}
        <div className="flex-1 space-y-3">
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
              1. Fault Injection Simulator
            </span>
            {hasFault ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-red-950/60 text-red-400 border border-red-800/60 animate-pulse">
                <AlertTriangle className="h-3 w-3" />
                Active Fault: {activeFaults.join(', ')}
              </span>
            ) : (
              <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-zinc-800/80 text-zinc-400 border border-zinc-700/50">
                Baseline Healthy
              </span>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              disabled={isInvestigating}
              className="h-9 px-3 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-200 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-400 focus:border-zinc-700 disabled:opacity-50 cursor-pointer"
            >
              <option value="invalid_db_config">Scenario 1: DB Config Drift (Port 9999)</option>
              <option value="db_unavailable">Scenario 2: Database Outage (Socket Refused)</option>
              <option value="high_latency">Scenario 3: Latency SLA Breach (+3000ms)</option>
              <option value="unsafe_proposal_sim">Scenario 4: Unsafe Action Injection (Governor Test)</option>
            </select>

            <button
              onClick={handleInject}
              disabled={isInvestigating}
              className="h-9 inline-flex items-center gap-1.5 px-3.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-medium transition-colors disabled:opacity-50"
            >
              <Zap className="h-3.5 w-3.5" />
              Inject Fault
            </button>

            <button
              onClick={onResetSimulator}
              disabled={isInvestigating}
              className="h-9 inline-flex items-center gap-1.5 px-3.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-zinc-800 text-xs font-medium transition-colors disabled:opacity-50"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Reset System
            </button>
          </div>
        </div>

        {/* Right Side: Agentic AI Runner */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3.5 lg:border-l lg:border-zinc-800/80 lg:pl-6 pt-3 lg:pt-0 border-t lg:border-t-0 border-zinc-800/60">
          <label className="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={forceFallback}
              onChange={(e) => setForceFallback(e.target.checked)}
              className="rounded bg-zinc-950 border-zinc-700 text-zinc-100 focus:ring-zinc-400 h-3.5 w-3.5 cursor-pointer accent-zinc-100"
            />
            <span>Deterministic Mode</span>
          </label>

          <button
            onClick={() => onRunInvestigation(forceFallback)}
            disabled={isInvestigating}
            className="w-full sm:w-auto h-10 inline-flex items-center justify-center gap-2 px-5 rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 font-semibold text-xs tracking-tight shadow-sm transition-all transform active:scale-98 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isInvestigating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-zinc-950" />
                <span>Running Workflow...</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>Run AI Investigation</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
