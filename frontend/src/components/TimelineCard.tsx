import React from 'react';
import { Clock, Terminal } from 'lucide-react';
import type { WorkflowTimelineEvent } from '../types/api';

interface TimelineCardProps {
  timeline: WorkflowTimelineEvent[];
}

export const TimelineCard: React.FC<TimelineCardProps> = ({ timeline }) => {
  const formatTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-4 shadow-sm h-full flex flex-col">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-zinc-400" />
          <span className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
            LangGraph Execution Timeline
          </span>
        </div>
        <span className="text-[11px] font-mono text-zinc-400 px-2 py-0.5 rounded bg-zinc-950 border border-zinc-800">
          {timeline.length} Graph Events
        </span>
      </div>

      {timeline.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-zinc-500 text-xs">
          <Clock className="w-8 h-8 text-zinc-700 mb-2" />
          <span>Timeline is idle. Run an AI investigation above to stream node execution events.</span>
        </div>
      ) : (
        <div className="space-y-3 overflow-y-auto max-h-[520px] pr-1">
          <div className="relative pl-5 border-l border-zinc-800 space-y-4 my-1">
            {timeline.map((event, idx) => (
              <div key={idx} className="relative">
                {/* Node bullet */}
                <div className="absolute -left-[25px] top-1 h-2.5 w-2.5 rounded-full bg-zinc-700 border-2 border-zinc-950" />

                <div className="flex items-baseline justify-between gap-2">
                  <span className="text-xs font-semibold text-zinc-200">
                    {event.stage}
                  </span>
                  <span className="text-[10px] font-mono text-zinc-400">
                    {formatTime(event.timestamp)}
                  </span>
                </div>

                <div className="text-xs text-zinc-400 mt-1 leading-relaxed">
                  {event.summary}
                </div>

                {event.details && Object.keys(event.details).length > 0 && (
                  <pre className="mt-1.5 p-2 rounded bg-zinc-950/80 border border-zinc-800/80 text-[10px] text-zinc-400 font-mono overflow-x-auto">
                    {JSON.stringify(event.details, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
