import { useEffect, useState } from 'react';
import { api } from './api/client';
import { BenchmarkCard } from './components/BenchmarkCard';
import { ControlPanel } from './components/ControlPanel';
import { DiagnosticsRibbon } from './components/DiagnosticsRibbon';
import { Header } from './components/Header';
import { HypothesisCard } from './components/HypothesisCard';
import { SafetyGovernorCard } from './components/SafetyGovernorCard';
import { TimelineCard } from './components/TimelineCard';
import { VerificationCard } from './components/VerificationCard';
import type {
  AgentStatusResponse,
  ClinicHealthResponse,
  DiagnosticReport,
  EvaluationReport,
  WorkflowRunResponse,
} from './types/api';

function App() {
  const [health, setHealth] = useState<ClinicHealthResponse | null>(null);
  const [report, setReport] = useState<DiagnosticReport | null>(null);
  const [activeFaults, setActiveFaults] = useState<string[]>([]);
  const [agentStatus, setAgentStatus] = useState<AgentStatusResponse | null>(null);
  const [workflowResult, setWorkflowResult] = useState<WorkflowRunResponse | null>(null);
  const [benchmarkReport, setBenchmarkReport] = useState<EvaluationReport | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isInvestigating, setIsInvestigating] = useState<boolean>(false);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Initial load
  const loadDashboardData = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [healthData, reportData, faultsData, statusData] = await Promise.all([
        api.getClinicHealth(),
        api.getDiagnosticReport(),
        api.getActiveFaults(),
        api.getAgentStatus(),
      ]);

      setHealth(healthData);
      setReport(reportData);
      setActiveFaults(faultsData.active_faults);
      setAgentStatus(statusData);

      // Attempt to load benchmark results in background
      api.getBenchmarkResults().then(setBenchmarkReport).catch(() => {});
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to connect to backend';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Handlers
  const handleInjectFault = async (faultType: string, params: Record<string, unknown>) => {
    try {
      setErrorMessage(null);
      await api.injectFault(faultType, params);
      await loadDashboardData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to inject fault';
      setErrorMessage(msg);
    }
  };

  const handleResetSimulator = async () => {
    try {
      setErrorMessage(null);
      await api.resetFaults();
      setWorkflowResult(null);
      await loadDashboardData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to reset simulator';
      setErrorMessage(msg);
    }
  };

  const handleRunInvestigation = async (forceFallback: boolean) => {
    setIsInvestigating(true);
    setErrorMessage(null);
    try {
      const result = await api.runWorkflow(
        'Operator requested automated incident response investigation',
        forceFallback,
        3
      );
      setWorkflowResult(result);
      await loadDashboardData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to complete workflow run';
      setErrorMessage(msg);
    } finally {
      setIsInvestigating(false);
    }
  };

  const handleRunBenchmark = async () => {
    setIsRunningBenchmark(true);
    setErrorMessage(null);
    try {
      const reportData = await api.runBenchmark();
      setBenchmarkReport(reportData);
      await loadDashboardData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to run benchmark suite';
      setErrorMessage(msg);
    } finally {
      setIsRunningBenchmark(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased selection:bg-emerald-500 selection:text-slate-950">
      {/* 1. Header Bar */}
      <Header
        health={health}
        agentStatus={agentStatus}
        loading={isLoading}
        onRefresh={loadDashboardData}
      />

      {/* 2. Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Error Notification Banner */}
        {errorMessage && (
          <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-sm flex items-start gap-3 shadow-lg">
            <span className="text-rose-400 font-bold">Error:</span>
            <span className="flex-1 leading-snug">{errorMessage}</span>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-400 hover:text-white text-xs font-semibold px-2 py-0.5 rounded bg-rose-900/50"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Control Room Panel: Scenario Selector & Trigger */}
        <ControlPanel
          activeFaults={activeFaults}
          isInvestigating={isInvestigating}
          onInjectFault={handleInjectFault}
          onResetSimulator={handleResetSimulator}
          onRunInvestigation={handleRunInvestigation}
        />

        {/* Live Diagnostics Ribbon (4 stat cards) */}
        <DiagnosticsRibbon report={report} loading={isLoading} />

        {/* Two-Column Operational Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Hypothesis, Safety Gate, Verification (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <HypothesisCard
              recommendation={workflowResult?.planner_recommendation ?? null}
              hypothesis={workflowResult?.hypothesis ?? ''}
            />

            <SafetyGovernorCard
              governorDecision={workflowResult?.governor_decision ?? null}
              proposedAction={workflowResult?.planner_recommendation?.recovery_action ?? null}
            />

            <VerificationCard
              verificationResult={workflowResult?.verification_result ?? null}
              overallStatus={workflowResult?.status ?? 'IDLE'}
            />
          </div>

          {/* Right Column: Audit Timeline (5 cols) */}
          <div className="lg:col-span-5">
            <TimelineCard timeline={workflowResult?.timeline ?? []} />
          </div>
        </div>

        {/* Evaluation & Benchmark Comparison Section */}
        <BenchmarkCard
          report={benchmarkReport}
          isRunningBenchmark={isRunningBenchmark}
          onRunBenchmark={handleRunBenchmark}
        />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 px-6 py-4 text-center text-xs text-slate-400">
        CivicShield Control Room — Safety-Governed Hybrid Agentic AI Prototype (Synthetic Simulation Mode)
      </footer>
    </div>
  );
}

export default App;
