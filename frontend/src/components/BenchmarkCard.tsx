import React from 'react';
import { BarChart3, RotateCw, CheckCircle2, XCircle } from 'lucide-react';
import type { EvaluationReport } from '../types/api';

interface BenchmarkCardProps {
  report: EvaluationReport | null;
  isRunningBenchmark: boolean;
  onRunBenchmark: () => void;
}

export const BenchmarkCard: React.FC<BenchmarkCardProps> = ({
  report,
  isRunningBenchmark,
  onRunBenchmark,
}) => {
  if (!report) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-6 text-center space-y-3">
        <div className="flex justify-center">
          <BarChart3 className="h-6 w-6 text-zinc-600" />
        </div>
        <div className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
          Empirical Benchmark & Evaluation
        </div>
        <p className="text-xs text-zinc-500 max-w-md mx-auto">
          No benchmark data loaded yet. Run the benchmark suite to empirically compare CivicShield against a blind restart baseline.
        </p>
        <button
          onClick={onRunBenchmark}
          disabled={isRunningBenchmark}
          className="h-8 px-4 rounded-lg bg-zinc-100 hover:bg-zinc-200 text-zinc-950 font-semibold text-xs transition-colors disabled:opacity-50"
        >
          {isRunningBenchmark ? 'Running Trials...' : 'Run Benchmark Trials'}
        </button>
      </div>
    );
  }

  const { civicshield_metrics: cs, baseline_metrics: bl, scenario_runs } = report;

  const scenarioNames = ['invalid_db_config', 'db_unavailable', 'high_latency', 'adversarial_unsafe'];

  const getScenarioLabel = (sc: string) => {
    switch (sc) {
      case 'invalid_db_config':
        return '1. DB Config Drift';
      case 'db_unavailable':
        return '2. DB Server Outage';
      case 'high_latency':
        return '3. Latency SLA Breach';
      case 'adversarial_unsafe':
        return '4. Unsafe Action Injection';
      default:
        return sc;
    }
  };

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 space-y-6 shadow-sm">
      {/* Header & Trigger */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-zinc-300" />
            <h3 className="text-sm font-semibold text-zinc-100">
              Evaluation: CivicShield vs. Blind Restart Baseline
            </h3>
          </div>
          <p className="text-xs text-zinc-500 mt-0.5">
            Empirical comparative analysis across {report.sample_size} automated trials
          </p>
        </div>

        <button
          onClick={onRunBenchmark}
          disabled={isRunningBenchmark}
          className="h-8 inline-flex items-center gap-1.5 px-3.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700/60 text-xs font-medium transition-colors disabled:opacity-50"
        >
          <RotateCw className={`h-3.5 w-3.5 ${isRunningBenchmark ? 'animate-spin' : ''}`} />
          {isRunningBenchmark ? 'Running Trials...' : 'Re-run Benchmark'}
        </button>
      </div>

      {/* 4 Metric Comparison Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-800/80">
          <div className="text-[11px] text-zinc-500 font-medium uppercase">Recovery Success Rate</div>
          <div className="text-2xl font-semibold text-zinc-100 mt-1">
            {cs.recovery_success_rate.toFixed(1)}%
          </div>
          <div className="text-xs text-zinc-400 mt-1 flex items-center justify-between">
            <span>Baseline:</span>
            <span className="font-mono">{bl.recovery_success_rate.toFixed(1)}%</span>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-800/80">
          <div className="text-[11px] text-zinc-500 font-medium uppercase">Root Cause Identification</div>
          <div className="text-2xl font-semibold text-zinc-100 mt-1">
            {cs.root_cause_accuracy.toFixed(1)}%
          </div>
          <div className="text-xs text-zinc-400 mt-1 flex items-center justify-between">
            <span>Baseline:</span>
            <span className="font-mono text-zinc-500">0.0% (Blind)</span>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-800/80">
          <div className="text-[11px] text-zinc-500 font-medium uppercase">Unsafe Action Block Rate</div>
          <div className="text-2xl font-semibold text-emerald-400 mt-1">
            {cs.unsafe_action_rejection_rate.toFixed(1)}%
          </div>
          <div className="text-xs text-zinc-400 mt-1 flex items-center justify-between">
            <span>Baseline:</span>
            <span className="font-mono text-red-400">0.0% (Unchecked)</span>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-800/80">
          <div className="text-[11px] text-zinc-500 font-medium uppercase">Futile Attempts</div>
          <div className="text-2xl font-semibold text-zinc-100 mt-1">
            {cs.total_unnecessary_attempts}
          </div>
          <div className="text-xs text-zinc-400 mt-1 flex items-center justify-between">
            <span>Baseline:</span>
            <span className="font-mono text-red-400">{bl.total_unnecessary_attempts} wasted</span>
          </div>
        </div>
      </div>

      {/* Comparison Data Table */}
      <div className="rounded-lg border border-zinc-800 overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-zinc-950 text-zinc-400 border-b border-zinc-800">
            <tr>
              <th className="py-2.5 px-4 font-medium">Fault Scenario</th>
              <th className="py-2.5 px-4 font-medium">CivicShield Recovery</th>
              <th className="py-2.5 px-4 font-medium">Baseline Recovery</th>
              <th className="py-2.5 px-4 font-medium">Attempts Used</th>
              <th className="py-2.5 px-4 font-medium">Outcome Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60 bg-zinc-900/30">
            {scenarioNames.map((sName) => {
              const csRun = scenario_runs.find((r) => r.system === 'civicshield' && r.scenario === sName);
              const blRun = scenario_runs.find((r) => r.system === 'baseline_restart' && r.scenario === sName);

              return (
                <tr key={sName} className="hover:bg-zinc-800/30 transition-colors">
                  <td className="py-3 px-4 font-medium text-zinc-200">
                    {getScenarioLabel(sName)}
                  </td>
                  <td className="py-3 px-4">
                    {csRun?.recovered ? (
                      <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Recovered
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-red-400 font-medium">
                        <XCircle className="h-3.5 w-3.5" /> Blocked/Escalated
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    {blRun?.recovered ? (
                      <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Recovered
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-zinc-500">
                        <XCircle className="h-3.5 w-3.5" /> Failed
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-zinc-300">
                    {csRun?.attempts_used ?? 1} attempt(s)
                  </td>
                  <td className="py-3 px-4 text-zinc-400 truncate max-w-xs">
                    {csRun?.details || '-'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
