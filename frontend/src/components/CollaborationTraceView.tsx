import * as React from 'react';
import {
  Activity,
  Bot,
  Brain,
  CheckCircle2,
  Cpu,
  Download,
  FileCode,
  GitBranch,
  HandMetal,
  PauseCircle,
  Shield,
  ShieldAlert,
  Sparkles,
  Terminal,
  UserCheck,
  WrapText,
  XCircle,
} from 'lucide-react';
import type { ExecutionEvent } from '../types/api';
import { Button } from './ui/button';
import {
  CodeBlock,
  CodeBlockActions,
  CodeBlockContent,
  CodeBlockCopyButton,
  CodeBlockHeader,
  CodeBlockLine,
  CodeBlockTitle,
} from './ui/code-block';
import { useHighlightedCode } from '../hooks/use-highlighted-code';

interface CollaborationTraceViewProps {
  events: ExecutionEvent[];
  autonomyMode?: string;
  workflowStatus?: string;
}

export function CollaborationTraceView({
  events,
  autonomyMode = 'autonomous',
  workflowStatus = 'IDLE',
}: CollaborationTraceViewProps) {
  const [selectedEventId, setSelectedEventId] = React.useState<string | null>(null);
  const [filterType, setFilterType] = React.useState<string>('all');
  const [wrapCode, setWrapCode] = React.useState<boolean>(false);

  // Auto-select first event or keep selection valid
  React.useEffect(() => {
    if (events.length > 0 && (!selectedEventId || !events.some((e) => e.event_id === selectedEventId))) {
      setSelectedEventId(events[0].event_id);
    }
  }, [events, selectedEventId]);

  const selectedEvent = events.find((e) => e.event_id === selectedEventId) || events[0] || null;

  const filteredEvents = React.useMemo(() => {
    if (filterType === 'all') return events;
    return events.filter((e) => e.agent_type === filterType);
  }, [events, filterType]);

  const totalDurationMs = React.useMemo(() => {
    return events.reduce((sum, e) => sum + (e.duration_ms || 0), 0);
  }, [events]);

  const agentCounts = React.useMemo(() => {
    const uniqueAgents = new Set(events.map((e) => e.agent_id));
    return uniqueAgents.size;
  }, [events]);

  // JSON string for selected event codeblock
  const selectedJsonString = React.useMemo(() => {
    if (!selectedEvent) return '{}';
    return JSON.stringify(
      {
        event_id: selectedEvent.event_id,
        run_id: selectedEvent.run_id,
        seq: selectedEvent.seq,
        timestamp: selectedEvent.timestamp,
        node: selectedEvent.node,
        agent_id: selectedEvent.agent_id,
        agent_type: selectedEvent.agent_type,
        event_type: selectedEvent.event_type,
        status: selectedEvent.status,
        duration_ms: selectedEvent.duration_ms,
        handoff_to: selectedEvent.handoff_to,
        input_summary: selectedEvent.input_summary,
        output_summary: selectedEvent.output_summary,
        structured_payload: selectedEvent.structured_payload,
        error_detail: selectedEvent.error_detail,
      },
      null,
      2
    );
  }, [selectedEvent]);

  const highlightedLines = useHighlightedCode(selectedJsonString, 'json');

  const downloadJson = (data: string, filename: string) => {
    const url = URL.createObjectURL(new Blob([data], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  const getAgentTypeBadge = (type: string) => {
    switch (type) {
      case 'ai_agent':
        return {
          label: 'AI Agent',
          icon: <Brain className="h-3 w-3 text-sky-400" />,
          badgeClass: 'bg-sky-950/70 border-sky-800 text-sky-300',
        };
      case 'deterministic_guardrail':
        return {
          label: 'Deterministic Guardrail',
          icon: <Shield className="h-3 w-3 text-amber-400" />,
          badgeClass: 'bg-amber-950/70 border-amber-800 text-amber-300',
        };
      case 'deterministic_tool':
        return {
          label: 'Deterministic Tool',
          icon: <Cpu className="h-3 w-3 text-purple-400" />,
          badgeClass: 'bg-purple-950/70 border-purple-800 text-purple-300',
        };
      case 'workflow_controller':
        return {
          label: 'Workflow Controller',
          icon: <GitBranch className="h-3 w-3 text-zinc-400" />,
          badgeClass: 'bg-zinc-900 border-zinc-700 text-zinc-300',
        };
      case 'human_operator':
        return {
          label: 'Human Operator',
          icon: <UserCheck className="h-3 w-3 text-emerald-400" />,
          badgeClass: 'bg-emerald-950/70 border-emerald-800 text-emerald-300',
        };
      default:
        return {
          label: type,
          icon: <Activity className="h-3 w-3 text-zinc-400" />,
          badgeClass: 'bg-zinc-900 border-zinc-800 text-zinc-400',
        };
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-950/60 border border-emerald-800 text-emerald-400">
            <CheckCircle2 className="h-2.5 w-2.5" />
            SUCCESS
          </span>
        );
      case 'blocked':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-red-950/60 border border-red-800 text-red-400">
            <ShieldAlert className="h-2.5 w-2.5" />
            BLOCKED
          </span>
        );
      case 'paused':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-amber-950/60 border border-amber-800 text-amber-400">
            <PauseCircle className="h-2.5 w-2.5" />
            PAUSED
          </span>
        );
      case 'escalated':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-rose-950/60 border border-rose-800 text-rose-400">
            <XCircle className="h-2.5 w-2.5" />
            ESCALATED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-zinc-900 border border-zinc-800 text-zinc-400">
            {status.toUpperCase()}
          </span>
        );
    }
  };

  if (events.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-10 text-center space-y-4">
        <div className="inline-flex p-3 rounded-full bg-zinc-800 text-zinc-400">
          <Bot className="h-6 w-6" />
        </div>
        <div className="max-w-md mx-auto space-y-2">
          <h3 className="text-sm font-semibold text-zinc-200">No Agent Collaboration Trace Available</h3>
          <p className="text-xs text-zinc-500 leading-relaxed">
            Run an investigation from the Control Room above to record real-time multi-agent telemetry between the
            Telemetry Collector, Diagnostic Analyst, Recovery Planner, and Safety Governor.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 1. Header Overview & Telemetry Bar */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-5 space-y-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-800/80 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-sky-950/60 border border-sky-800 text-sky-400">
              <Bot className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-zinc-100">Multi-Agent Collaboration Trace</h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                  Run ID: {events[0]?.run_id || 'N/A'}
                </span>
              </div>
              <p className="text-xs text-zinc-500">
                Chronological telemetry of agent handoffs, deterministic guardrail evaluations, and tool calls.
              </p>
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="flex items-center gap-2">
            <div className="px-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-center">
              <div className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono">Agents</div>
              <div className="text-xs font-semibold text-zinc-200">{agentCounts} Active</div>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-center">
              <div className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono">Events</div>
              <div className="text-xs font-semibold text-zinc-200">{events.length} Steps</div>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-center">
              <div className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono">Duration</div>
              <div className="text-xs font-semibold text-sky-400 font-mono">{totalDurationMs.toFixed(1)} ms</div>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-center">
              <div className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono">Mode</div>
              <div className="text-xs font-semibold text-zinc-300 uppercase">{autonomyMode}</div>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 text-center">
              <div className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono">Status</div>
              <div className="text-xs font-semibold text-emerald-400 font-mono">{workflowStatus}</div>
            </div>
          </div>
        </div>

        {/* Multi-Agent Architecture Chain Diagram */}
        <div className="overflow-x-auto pb-1 pt-1 custom-scrollbar">
          <div className="flex items-center gap-1.5 min-w-max text-[11px] font-mono">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-950 border border-zinc-800 text-zinc-400">
              <GitBranch className="h-3 w-3 text-zinc-500" />
              <span>Intake</span>
            </div>
            <span className="text-zinc-600 font-bold">&rarr;</span>

            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-purple-950/40 border border-purple-900/60 text-purple-300">
              <Cpu className="h-3 w-3 text-purple-400" />
              <span>Telemetry Collector</span>
            </div>
            <span className="text-zinc-600 font-bold">&rarr;</span>

            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-sky-950/50 border border-sky-800/70 text-sky-300">
              <Brain className="h-3 w-3 text-sky-400" />
              <span>Diagnostic Analyst</span>
            </div>
            <span className="text-zinc-600 font-bold">&rarr;</span>

            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-indigo-950/50 border border-indigo-800/70 text-indigo-300">
              <Sparkles className="h-3 w-3 text-indigo-400" />
              <span>Recovery Planner</span>
            </div>
            <span className="text-zinc-600 font-bold">&rarr;</span>

            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-950/50 border border-amber-800/70 text-amber-300">
              <Shield className="h-3 w-3 text-amber-400" />
              <span>Safety Governor</span>
            </div>
            <span className="text-zinc-600 font-bold">&rarr;</span>

            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-teal-950/40 border border-teal-900/60 text-teal-300">
              <HandMetal className="h-3 w-3 text-teal-400" />
              <span>Executor / Human</span>
            </div>
            <span className="text-zinc-600 font-bold">&rarr;</span>

            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-950/40 border border-emerald-900/60 text-emerald-300">
              <CheckCircle2 className="h-3 w-3 text-emerald-400" />
              <span>Verification Probe</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Filter & Navigation Toolbar */}
      <div className="flex items-center justify-between gap-3">
        <div className="inline-flex p-1 rounded-lg bg-zinc-900 border border-zinc-800 text-xs">
          <button
            onClick={() => setFilterType('all')}
            className={`px-3 py-1 rounded-md font-medium transition-colors ${
              filterType === 'all' ? 'bg-zinc-100 text-zinc-950 shadow-sm' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            All Steps ({events.length})
          </button>
          <button
            onClick={() => setFilterType('ai_agent')}
            className={`px-3 py-1 rounded-md font-medium transition-colors ${
              filterType === 'ai_agent' ? 'bg-sky-500 text-zinc-950 shadow-sm' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            AI Agents
          </button>
          <button
            onClick={() => setFilterType('deterministic_guardrail')}
            className={`px-3 py-1 rounded-md font-medium transition-colors ${
              filterType === 'deterministic_guardrail'
                ? 'bg-amber-400 text-zinc-950 shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Guardrails
          </button>
          <button
            onClick={() => setFilterType('deterministic_tool')}
            className={`px-3 py-1 rounded-md font-medium transition-colors ${
              filterType === 'deterministic_tool'
                ? 'bg-purple-400 text-zinc-950 shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Tools
          </button>
          <button
            onClick={() => setFilterType('workflow_controller')}
            className={`px-3 py-1 rounded-md font-medium transition-colors ${
              filterType === 'workflow_controller'
                ? 'bg-zinc-300 text-zinc-950 shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Controllers
          </button>
        </div>

        <span className="text-xs text-zinc-500 font-mono">
          Showing {filteredEvents.length} of {events.length} telemetry records
        </span>
      </div>

      {/* 3. Split Layout: Interactive Event Timeline & Deep CodeBlock Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Sequential Handoff Event Cards (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          {filteredEvents.map((event) => {
            const isSelected = event.event_id === selectedEventId;
            const badge = getAgentTypeBadge(event.agent_type);

            return (
              <div
                key={event.event_id}
                onClick={() => setSelectedEventId(event.event_id)}
                className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-zinc-900 border-zinc-400 shadow-md ring-1 ring-zinc-500/30'
                    : 'bg-zinc-950/90 border-zinc-800/80 hover:bg-zinc-900/60 hover:border-zinc-700'
                }`}
              >
                {/* Header: Seq, Agent ID, Duration & Status */}
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px] font-semibold text-zinc-500 px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800">
                      #{String(event.seq).padStart(2, '0')}
                    </span>
                    <span className="font-semibold text-zinc-200 font-mono text-[12px]">{event.agent_id}</span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {event.duration_ms !== null && (
                      <span className="font-mono text-[10px] text-zinc-500">{event.duration_ms} ms</span>
                    )}
                    {getStatusBadge(event.status)}
                  </div>
                </div>

                {/* Subheader: Node & Agent Type Badge */}
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] border font-medium ${badge.badgeClass}`}
                  >
                    {badge.icon}
                    {badge.label}
                  </span>
                  <span className="text-[11px] text-zinc-500 font-mono">Node: {event.node}</span>
                </div>

                {/* Output Summary */}
                <p className="text-zinc-300 text-[11px] leading-relaxed line-clamp-2 mb-2">
                  {event.output_summary}
                </p>

                {/* Handoff Target */}
                {event.handoff_to && (
                  <div className="flex items-center gap-1 text-[10px] text-zinc-500 font-mono border-t border-zinc-850 pt-2">
                    <span className="text-zinc-600">Handoff:</span>
                    <span className="text-sky-400 font-medium">{event.handoff_to}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Right Column: In-Depth Agent Telemetry & CodeBlock Inspector (7 cols) */}
        <div className="lg:col-span-7 sticky top-6 space-y-4">
          {selectedEvent ? (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/80 p-5 space-y-4 shadow-sm">
              {/* Header */}
              <div className="flex items-start justify-between gap-4 border-b border-zinc-800/80 pb-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-zinc-100 font-mono">{selectedEvent.agent_id}</span>
                    {getStatusBadge(selectedEvent.status)}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-zinc-400">
                    <span>Node: <strong className="text-zinc-300 font-mono">{selectedEvent.node}</strong></span>
                    <span>&bull;</span>
                    <span>Event Type: <strong className="text-zinc-300 font-mono">{selectedEvent.event_type}</strong></span>
                    <span>&bull;</span>
                    <span>Duration: <strong className="text-sky-400 font-mono">{selectedEvent.duration_ms} ms</strong></span>
                  </div>
                </div>

                <div className="text-right font-mono text-[11px] text-zinc-500">
                  Seq #{selectedEvent.seq}
                </div>
              </div>

              {/* Input Context Card */}
              <div className="rounded-lg border border-zinc-800/90 bg-zinc-950/70 p-3 space-y-1">
                <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">Input Summary</div>
                <p className="text-xs text-zinc-300 leading-relaxed font-sans">{selectedEvent.input_summary}</p>
              </div>

              {/* Output Decision Card */}
              <div className="rounded-lg border border-zinc-800/90 bg-zinc-950/70 p-3 space-y-1">
                <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">Output / Decision</div>
                <p className="text-xs text-zinc-200 leading-relaxed font-sans font-medium">
                  {selectedEvent.output_summary}
                </p>
              </div>

              {/* Handoff Target */}
              {selectedEvent.handoff_to && (
                <div className="flex items-center justify-between p-3 rounded-lg bg-sky-950/30 border border-sky-900/50 text-xs">
                  <span className="text-zinc-400">Next Handoff Destination:</span>
                  <span className="font-mono font-semibold text-sky-300">{selectedEvent.handoff_to}</span>
                </div>
              )}

              {/* Deep Telemetry Payload: Shadcn CodeBlock */}
              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-zinc-300 flex items-center gap-2">
                    <FileCode className="h-3.5 w-3.5 text-zinc-400" />
                    Structured Telemetry Payload
                  </span>
                  <span className="text-[10px] text-zinc-500 font-mono">Pydantic Schema Serialization</span>
                </div>

                <CodeBlock className="border-zinc-800 bg-zinc-950">
                  <CodeBlockHeader className="border-zinc-850 bg-zinc-900/60">
                    <CodeBlockTitle>
                      <Terminal className="h-3.5 w-3.5 text-zinc-400" />
                      {selectedEvent.agent_id}.json
                    </CodeBlockTitle>

                    <CodeBlockActions>
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => setWrapCode((prev) => !prev)}
                        className={`text-zinc-400 hover:text-zinc-100 ${wrapCode ? 'bg-zinc-800 text-zinc-200' : ''}`}
                        title={wrapCode ? 'Disable wrap' : 'Enable word wrap'}
                      >
                        <WrapText className="h-3.5 w-3.5" />
                      </Button>

                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() =>
                          downloadJson(
                            selectedJsonString,
                            `${selectedEvent.agent_id}-event-${selectedEvent.seq}.json`
                          )
                        }
                        className="text-zinc-400 hover:text-zinc-100"
                        title="Download JSON telemetry"
                      >
                        <Download className="h-3.5 w-3.5" />
                      </Button>

                      <CodeBlockCopyButton value={selectedJsonString} />
                    </CodeBlockActions>
                  </CodeBlockHeader>

                  <CodeBlockContent wrap={wrapCode} lineNumbers={true} className="max-h-[380px]">
                    {highlightedLines.map((line, idx) => (
                      <CodeBlockLine key={idx} lineNumber={idx + 1}>
                        {line}
                      </CodeBlockLine>
                    ))}
                  </CodeBlockContent>
                </CodeBlock>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-8 text-center text-xs text-zinc-500">
              Select an event from the timeline to inspect its structured telemetry payload.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
