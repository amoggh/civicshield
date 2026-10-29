import * as React from 'react';
import {
  Clock,
  Terminal,
  FileCode,
  WrapText,
  Download,
  ArrowRight,
  Info,
} from 'lucide-react';
import type { WorkflowTimelineEvent } from '../types/api';
import { Button } from './ui/button';
import {
  CodeBlock,
  CodeBlockHeader,
  CodeBlockTitle,
  CodeBlockActions,
  CodeBlockCopyButton,
  CodeBlockContent,
  CodeBlockLine,
} from './ui/code-block';
import { useHighlightedCode } from '../hooks/use-highlighted-code';

interface TimelineCardProps {
  timeline: WorkflowTimelineEvent[];
}

interface NodeMeta {
  title: string;
  simpleExplanation: string;
  bgBadge: string;
  borderBadge: string;
  textColor: string;
  dotColor: string;
  ringColor: string;
}

const STAGE_META: Record<string, NodeMeta> = {
  INTAKE: {
    title: 'Incident Intake',
    simpleExplanation:
      'Captures the incident alert, initializes the LangGraph state machine, and resets retry attempt counters to start the investigation.',
    bgBadge: 'bg-purple-950/60',
    borderBadge: 'border-purple-800',
    textColor: 'text-purple-300',
    dotColor: 'bg-purple-400',
    ringColor: 'ring-purple-500/30',
  },
  DIAGNOSE: {
    title: 'Diagnostic Suite',
    simpleExplanation:
      'Executes all 5 deterministic diagnostic tools (health ping, DB socket check, config diff, latency SLA probe, log scanner) to collect empirical evidence.',
    bgBadge: 'bg-blue-950/60',
    borderBadge: 'border-blue-800',
    textColor: 'text-blue-300',
    dotColor: 'bg-blue-400',
    ringColor: 'ring-blue-500/30',
  },
  PLAN: {
    title: 'AI Investigator & Planner',
    simpleExplanation:
      'Supplies structured evidence to Google Gemini (or Deterministic Fallback) via LangChain to formulate a root cause hypothesis and propose an allowlisted recovery action.',
    bgBadge: 'bg-indigo-950/60',
    borderBadge: 'border-indigo-800',
    textColor: 'text-indigo-300',
    dotColor: 'bg-indigo-400',
    ringColor: 'ring-indigo-500/30',
  },
  SAFETY_CHECK: {
    title: 'Deterministic Safety Governor',
    simpleExplanation:
      'A non-LLM security barrier that validates the AI proposal against a strict allowlist, blocks destructive syntax, confirms matching evidence, and caps retries at 3.',
    bgBadge: 'bg-amber-950/60',
    borderBadge: 'border-amber-800',
    textColor: 'text-amber-300',
    dotColor: 'bg-amber-400',
    ringColor: 'ring-amber-500/30',
  },
  EXECUTE: {
    title: 'Simulator Action Executor',
    simpleExplanation:
      'Directly executes the approved safe remediation action on the clinic simulator (e.g. restoring baseline port 5432 or clearing injected latency).',
    bgBadge: 'bg-teal-950/60',
    borderBadge: 'border-teal-800',
    textColor: 'text-teal-300',
    dotColor: 'bg-teal-400',
    ringColor: 'ring-teal-500/30',
  },
  VERIFY: {
    title: 'Post-Repair Verification Probe',
    simpleExplanation:
      'Performs an end-to-end synthetic appointment booking probe to guarantee clinic appointments can actually be booked before declaring recovery.',
    bgBadge: 'bg-emerald-950/60',
    borderBadge: 'border-emerald-800',
    textColor: 'text-emerald-300',
    dotColor: 'bg-emerald-400',
    ringColor: 'ring-emerald-500/30',
  },
  ESCALATE: {
    title: 'Human SRE Escalation',
    simpleExplanation:
      'Triggered when an unsafe action is detected, safety checks fail, or retries exceed 3 attempts. Immediately stops autonomous intervention and pages on-call human engineers.',
    bgBadge: 'bg-rose-950/60',
    borderBadge: 'border-rose-800',
    textColor: 'text-rose-300',
    dotColor: 'bg-rose-400',
    ringColor: 'ring-rose-500/30',
  },
};

function downloadJson(value: string, filename: string) {
  const url = URL.createObjectURL(new Blob([value], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

// Inner CodeBlock View for Node Details
interface NodeDetailCodeBlockProps {
  stage: string;
  details: Record<string, unknown>;
}

const NodeDetailCodeBlock: React.FC<NodeDetailCodeBlockProps> = ({ stage, details }) => {
  const [wrap, setWrap] = React.useState(false);
  const jsonString = React.useMemo(() => JSON.stringify(details, null, 2), [details]);
  const lines = useHighlightedCode(jsonString, 'json');

  return (
    <div className="w-full">
      <CodeBlock>
        <CodeBlockHeader>
          <CodeBlockTitle>
            <FileCode className="h-3.5 w-3.5 text-zinc-400" />
            <span>{stage.toLowerCase()}_state_payload.json</span>
          </CodeBlockTitle>
          <CodeBlockActions>
            <Button
              variant="ghost"
              size="icon-xs"
              aria-label="Wrap lines"
              aria-pressed={wrap}
              className={wrap ? 'text-zinc-100 bg-zinc-800' : 'text-zinc-400'}
              onClick={() => setWrap(!wrap)}
              title="Toggle line wrapping"
            >
              <WrapText className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="icon-xs"
              aria-label="Download JSON"
              onClick={() => downloadJson(jsonString, `${stage.toLowerCase()}_event.json`)}
              title="Download event JSON"
            >
              <Download className="h-3.5 w-3.5" />
            </Button>
            <CodeBlockCopyButton value={jsonString} />
          </CodeBlockActions>
        </CodeBlockHeader>
        <CodeBlockContent wrap={wrap} lineNumbers>
          {lines.map((line, index) => (
            <CodeBlockLine key={index} lineNumber={index + 1}>
              {line}
            </CodeBlockLine>
          ))}
        </CodeBlockContent>
      </CodeBlock>
    </div>
  );
};

export const TimelineCard: React.FC<TimelineCardProps> = ({ timeline }) => {
  // Currently inspected event index (default to the last executed event or null)
  const [selectedIdx, setSelectedIdx] = React.useState<number | null>(null);

  // Auto-select latest event when timeline updates
  React.useEffect(() => {
    if (timeline.length > 0) {
      setSelectedIdx(timeline.length - 1);
    } else {
      setSelectedIdx(null);
    }
  }, [timeline.length]);

  const activeEvent = selectedIdx !== null && timeline[selectedIdx] ? timeline[selectedIdx] : null;
  const activeMeta = activeEvent ? (STAGE_META[activeEvent.stage] ?? STAGE_META.INTAKE) : null;

  const formatTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return isoString;
    }
  };

  // Standard LangGraph sequence of nodes for the interactive graph bar
  const graphNodes = ['INTAKE', 'DIAGNOSE', 'PLAN', 'SAFETY_CHECK', 'EXECUTE', 'VERIFY'];

  return (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-5 shadow-sm">
          {/* Top Header */}
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
            <div className="flex items-center gap-2">
                <Terminal className="h-4 w-4 text-zinc-300" />
                <span className="text-xs font-semibold text-zinc-100 uppercase tracking-wider">
                  Interactive LangGraph Workflow & Execution Inspector
                </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono text-zinc-400 px-2 py-0.5 rounded bg-zinc-950 border border-zinc-800">
                {timeline.length} Graph Events Recorded
              </span>
            </div>
          </div>

          {/* 1. Interactive LangGraph Flow Map Ribbon */}
          <div className="space-y-2">
            <div className="text-[11px] font-medium text-zinc-400 flex items-center gap-1.5">
              <Info className="h-3 w-3 text-zinc-500" />
              <span>LangGraph Node Pipeline (Hover or click any node to inspect execution details):</span>
            </div>

            <div className="flex items-center gap-1.5 overflow-x-auto py-2 px-1">
              {graphNodes.map((stageKey, idx) => {
                const meta = STAGE_META[stageKey] ?? STAGE_META.INTAKE;
                // Find if this stage has an executed event in timeline
                const executedEventIdx = timeline.findIndex((e) => e.stage === stageKey);
                const isExecuted = executedEventIdx !== -1;
                const isCurrentlySelected = activeEvent?.stage === stageKey;

                return (
                  <React.Fragment key={stageKey}>
                    <button
                      onClick={() => {
                        if (isExecuted) setSelectedIdx(executedEventIdx);
                      }}
                      onMouseEnter={() => {
                        if (isExecuted) setSelectedIdx(executedEventIdx);
                      }}
                      className={`group relative flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all cursor-pointer ${isCurrentlySelected
                          ? `${meta.bgBadge} ${meta.borderBadge} ${meta.textColor} ring-2 ${meta.ringColor} shadow-md`
                          : isExecuted
                            ? 'bg-zinc-900 border-zinc-700/80 text-zinc-300 hover:border-zinc-500'
                            : 'bg-zinc-950/40 border-zinc-900 text-zinc-600 cursor-not-allowed opacity-60'
                        }`}
                      title={`${meta.title} — ${meta.simpleExplanation}`}
                    >
                      <span
                        className={`h-2 w-2 rounded-full ${isExecuted ? meta.dotColor : 'bg-zinc-700'
                          } ${isCurrentlySelected ? 'animate-pulse' : ''}`}
                      />
                      <span>{meta.title}</span>
                      {isExecuted && (
                        <span className="text-[10px] font-mono opacity-60">
                          ✓
                        </span>
                      )}
                    </button>

                    {idx < graphNodes.length - 1 && (
                      <ArrowRight className="h-3.5 w-3.5 text-zinc-700 shrink-0" />
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>

          {/* Empty State when no events exist */}
          {timeline.length === 0 ? (
              <div className="flex flex-col items-center justify-center text-center p-10 text-zinc-500 text-xs rounded-xl border border-dashed border-zinc-800 bg-zinc-950/40">
                <Clock className="w-8 h-8 text-zinc-700 mb-2" />
                <span className="font-medium text-zinc-400">Timeline is in standby.</span>
                <span className="mt-1 text-zinc-600">Run an AI investigation from the Control Panel to trigger the LangGraph state machine.</span>
              </div>
              ) : (
        /* Two-Column Interactive Layout: Node History (Left) + Hover/Spawn Inspector with CodeBlock (Right) */
                      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
                        {/* Left Column: Timeline Node Feed (5 cols) */}
                        <div className="lg:col-span-5 space-y-2">
                          <div className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider mb-2">
                            Executed Events ({timeline.length})
                          </div>

                              <div className="space-y-2 max-h-[460px] overflow-y-auto pr-1 custom-scrollbar">
                                {timeline.map((event, idx) => {
                                  const meta = STAGE_META[event.stage] ?? STAGE_META.INTAKE;
                                  const isSelected = selectedIdx === idx;

                                  return (
                                    <div
                                      key={idx}
                                      onClick={() => setSelectedIdx(idx)}
                                      onMouseEnter={() => setSelectedIdx(idx)}
                                      className={`p-3 rounded-lg border text-xs transition-all cursor-pointer ${isSelected
                                          ? `${meta.bgBadge} ${meta.borderBadge} ring-1 ${meta.ringColor} shadow-sm`
                                          : 'bg-zinc-950/60 border-zinc-800/80 hover:bg-zinc-900/60 hover:border-zinc-700'
                                        }`}
                                    >
                                      <div className="flex items-center justify-between gap-2 mb-1">
                                        <div className="flex items-center gap-2">
                                          <span className={`h-2 w-2 rounded-full ${meta.dotColor}`} />
                                          <span className={`font-semibold ${isSelected ? meta.textColor : 'text-zinc-200'}`}>
                                            {event.stage}
                                          </span>
                                        </div>
                                        <span className="text-[10px] font-mono text-zinc-400">
                                          {formatTime(event.timestamp)}
                                        </span>
                                      </div>

                                      <p className="text-zinc-400 text-xs line-clamp-2 leading-relaxed">
                                        {event.summary}
                                      </p>

                                      <div className="mt-2 flex items-center justify-between text-[10px] text-zinc-400">
                                        <span>Event #{idx + 1}</span>
                                        <span className="font-medium text-zinc-300 group-hover:underline">
                                          {isSelected ? 'Inspecting →' : 'Click to inspect'}
                                        </span>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                          </div>

                          {/* Right Column: Spawned Node Detailed Inspector with CodeBlock (7 cols) */}
                          <div className="lg:col-span-7">
                            {activeEvent && activeMeta ? (
                              <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-5 space-y-4 shadow-md transition-all">
                                {/* Header with Title and Stage badge */}
                                <div className="flex items-start justify-between gap-3 border-b border-zinc-800/80 pb-3">
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <span className={`h-2.5 w-2.5 rounded-full ${activeMeta.dotColor} animate-pulse`} />
                                      <h4 className="text-sm font-semibold text-zinc-100">
                                        {activeMeta.title}
                                      </h4>
                                      <span
                                        className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${activeMeta.bgBadge} ${activeMeta.borderBadge} ${activeMeta.textColor}`}
                                      >
                                        {activeEvent.stage}
                                      </span>
                                    </div>
                                    <span className="text-[11px] font-mono text-zinc-400 mt-1 block">
                                      Executed at: {new Date(activeEvent.timestamp).toLocaleString()}
                                    </span>
                                  </div>

                                  <span className="text-[11px] text-zinc-400 font-mono px-2 py-1 rounded bg-zinc-900 border border-zinc-800">
                                    Step {selectedIdx! + 1} of {timeline.length}
                                  </span>
                                </div>

                                  {/* 1. Simple Plain-English Process Explanation */}
                                  <div className="p-3.5 rounded-lg bg-zinc-900/60 border border-zinc-800/80 space-y-1.5">
                                    <div className="text-[11px] font-semibold text-zinc-300 uppercase tracking-wider flex items-center gap-1.5">
                                      <Info className="h-3.5 w-3.5 text-zinc-400" />
                                      <span>What This Node Does (Simple Explanation):</span>
                                    </div>
                                    <p className="text-xs text-zinc-300 leading-relaxed font-normal">
                                      {activeMeta.simpleExplanation}
                                    </p>
                                  </div>

                                  {/* 2. Runtime Outcome Summary */}
                                  <div className="p-3 rounded-lg bg-zinc-900/40 border border-zinc-800/60 space-y-1">
                                    <span className="text-[11px] font-medium text-zinc-400">Node Execution Summary:</span>
                                    <div className="text-xs text-zinc-200 font-mono leading-relaxed">
                                      {activeEvent.summary}
                                    </div>
                                  </div>

                                  {/* 3. Shadcn CodeBlock Component showing State Payload */}
                                  <div className="space-y-1.5">
                                    <div className="text-[11px] font-medium text-zinc-400 flex items-center justify-between">
                                      <span>Structured JSON Response Payload:</span>
                                      <span className="text-[10px] text-zinc-400 font-mono">
                                        {Object.keys(activeEvent.details || {}).length} Fields Captured
                                      </span>
                                    </div>

                                    <NodeDetailCodeBlock
                                      stage={activeEvent.stage}
                                      details={activeEvent.details || {}}
                                    />
                                  </div>
                                </div>
                                ) : (
                                <div className="h-full flex items-center justify-center p-8 rounded-xl border border-dashed border-zinc-800 text-zinc-500 text-xs">
                                  Hover or select a node on the left to spawn its detailed explanation and JSON code block.
                                </div>
            )}
                              </div>
        </div>
      )}
                        </div>
                        );
};
