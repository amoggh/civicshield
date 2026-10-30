import { useEffect, useState } from 'react';
import { api } from './api/client';
import { BenchmarkCard } from './components/BenchmarkCard';
import { CollaborationTraceView } from './components/CollaborationTraceView';
import { ControlPanel } from './components/ControlPanel';
import { DiagnosticsRibbon } from './components/DiagnosticsRibbon';
import { Header } from './components/Header';
import { HypothesisCard } from './components/HypothesisCard';
import { SafetyGovernorCard } from './components/SafetyGovernorCard';
import { TimelineCard } from './components/TimelineCard';
import { VerificationCard } from './components/VerificationCard';
import { Sparkles, Terminal, BarChart3, AlertCircle, Bot } from 'lucide-react';
import type {
  AgentStatusResponse,
  AutonomyMode,
  ClinicHealthResponse,
  DiagnosticReport,
  EvaluationReport,
  WorkflowRunResponse,
} from './types/api';

type TabType = 'pipeline' | 'timeline' | 'trace' | 'benchmark';

function App() {
  const [health, setHealth] = useState<ClinicHealthResponse | null>(null);
  const [report, setReport] = useState<DiagnosticReport | null>(null);
  const [activeFaults, setActiveFaults] = useState<string[]>([]);
  const [agentStatus, setAgentStatus] = useState<AgentStatusResponse | null>(null);
  const [workflowResult, setWorkflowResult] = useState<WorkflowRunResponse | null>(null);
  const [benchmarkReport, setBenchmarkReport] = useState<EvaluationReport | null>(null);

  const [activeTab, setActiveTab] = useState<TabType>('pipeline');
  const [autonomyMode, setAutonomyMode] = useState<AutonomyMode>('autonomous');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isInvestigating, setIsInvestigating] = useState<boolean>(false);
  const [isResuming, setIsResuming] = useState<boolean>(false);
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
        autonomyMode,
        forceFallback,
        3
      );
      setWorkflowResult(result);
      // Auto-switch to pipeline tab so the user sees the 3 steps immediately
      setActiveTab('pipeline');
      await loadDashboardData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to complete workflow run';
      setErrorMessage(msg);
    } finally {
      setIsInvestigating(false);
    }
  };

  const handleResumeWorkflow = async (approved: boolean, reason?: string) => {
    if (!workflowResult) return;
    setIsResuming(true);
    setErrorMessage(null);
    try {
      const resumed = await api.resumeWorkflow({
        approved,
        rejection_reason: reason || null,
        paused_state: workflowResult as unknown as Record<string, unknown>,
      });
      setWorkflowResult(resumed);
      await loadDashboardData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to process operator decision';
      setErrorMessage(msg);
    } finally {
      setIsResuming(false);
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
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans selection:bg-zinc-800 selection:text-zinc-100">
      {/* 1. Header Bar */}
      <Header
        health={health}
        agentStatus={agentStatus}
        loading={isLoading}
        onRefresh={loadDashboardData}
      />

      {/* 2. Main Content Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Error Notification Banner */}
        {errorMessage && (
          <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-900/60 text-red-300 text-xs flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-400 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-red-400 hover:text-white text-xs font-semibold px-2 py-0.5 rounded bg-red-900/40"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Control Room Panel: Scenario Selector, Autonomy Modes, & Trigger */}
        <ControlPanel
          activeFaults={activeFaults}
          isInvestigating={isInvestigating}
          autonomyMode={autonomyMode}
          onAutonomyModeChange={setAutonomyMode}
          onInjectFault={handleInjectFault}
          onResetSimulator={handleResetSimulator}
          onRunInvestigation={handleRunInvestigation}
        />

        {/* Live Diagnostics Ribbon (4 stat cards) */}
        <DiagnosticsRibbon report={report} loading={isLoading} />

        {/* Minimalist Shadcn Tab Switcher */}
        <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
          <div className="inline-flex p-1 rounded-lg bg-zinc-900 border border-zinc-800 text-xs">
            <button
              onClick={() => setActiveTab('pipeline')}
              className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-md font-medium transition-all ${
                activeTab === 'pipeline'
                  ? 'bg-zinc-100 text-zinc-950 shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>AI Remediation Pipeline</span>
            </button>

            <button
              onClick={() => setActiveTab('timeline')}
              className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-md font-medium transition-all ${
                activeTab === 'timeline'
                  ? 'bg-zinc-100 text-zinc-950 shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Terminal className="h-3.5 w-3.5" />
              <span>Execution Timeline</span>
              {workflowResult && (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-zinc-800 text-zinc-300">
                  {workflowResult.timeline.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('trace')}
              className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-md font-medium transition-all ${
                activeTab === 'trace'
                  ? 'bg-zinc-100 text-zinc-950 shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Bot className="h-3.5 w-3.5" />
              <span>Agent Collaboration Trace</span>
              {workflowResult?.events && workflowResult.events.length > 0 && (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-sky-950 text-sky-400 border border-sky-800">
                  {workflowResult.events.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('benchmark')}
              className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-md font-medium transition-all ${
                activeTab === 'benchmark'
                  ? 'bg-zinc-100 text-zinc-950 shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <BarChart3 className="h-3.5 w-3.5" />
              <span>Benchmark Comparison</span>
            </button>
          </div>

          <div className="hidden sm:block text-xs text-zinc-500 font-mono">
            {workflowResult
              ? `Status: ${workflowResult.status} (${workflowResult.attempt_count} attempts) [${workflowResult.autonomy_mode ?? autonomyMode}]`
              : `Status: Ready [${autonomyMode}]`}
          </div>
        </div>

        {/* Tab 1: 3-Step Remediation Pipeline */}
        {activeTab === 'pipeline' && (
          <div className="space-y-4">
            <HypothesisCard
              recommendation={workflowResult?.planner_recommendation ?? null}
              hypothesis={workflowResult?.hypothesis ?? ''}
            />

            <SafetyGovernorCard
              governorDecision={workflowResult?.governor_decision ?? null}
              proposedAction={workflowResult?.planner_recommendation?.recovery_action ?? null}
              autonomyMode={workflowResult?.autonomy_mode ?? autonomyMode}
              awaitingApproval={workflowResult?.awaiting_approval ?? false}
              humanApproved={workflowResult?.human_approved ?? null}
              shadowMatchesExpected={workflowResult?.shadow_matches_expected ?? null}
              shadowExpectedAction={workflowResult?.shadow_expected_action ?? null}
              onApprove={() => handleResumeWorkflow(true)}
              onReject={(reason) => handleResumeWorkflow(false, reason)}
              isResuming={isResuming}
            />

            <VerificationCard
              verificationResult={workflowResult?.verification_result ?? null}
              overallStatus={workflowResult?.status ?? 'IDLE'}
            />
          </div>
        )}

        {/* Tab 2: Execution Timeline */}
        {activeTab === 'timeline' && (
          <div>
            <TimelineCard timeline={workflowResult?.timeline ?? []} />
          </div>
        )}

        {/* Tab 3: Multi-Agent Collaboration Trace */}
        {activeTab === 'trace' && (
          <div>
            <CollaborationTraceView
              events={workflowResult?.events ?? []}
              autonomyMode={workflowResult?.autonomy_mode ?? autonomyMode}
              workflowStatus={workflowResult?.status ?? 'IDLE'}
            />
          </div>
        )}

        {/* Tab 4: Evaluation Benchmark */}
        {activeTab === 'benchmark' && (
          <div>
            <BenchmarkCard
              report={benchmarkReport}
              isRunningBenchmark={isRunningBenchmark}
              onRunBenchmark={handleRunBenchmark}
            />
          </div>
        )}
      </main>

      {/* Minimal Footer */}
      <footer className="border-t border-zinc-900 bg-zinc-950 px-6 py-4 text-center text-xs text-zinc-600">
        CivicShield · Safety-Governed Hybrid Agentic AI Prototype (Synthetic Simulation Mode)
      </footer>
    </div>
  );
}

export default App;
