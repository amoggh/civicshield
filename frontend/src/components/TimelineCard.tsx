import React from 'react';
import type { WorkflowTimelineEvent } from '../types/api';

interface TimelineCardProps {
  timeline: WorkflowTimelineEvent[];
}

export const TimelineCard: React.FC<TimelineCardProps> = ({ timeline }) => {
  const getStageColor = (stage: string) => {
    switch (stage) {
      case 'INTAKE':
        return 'bg-purple-900/60 text-purple-300 border-purple-700';
      case 'DIAGNOSE':
        return 'bg-blue-900/60 text-blue-300 border-blue-700';
      case 'PLAN':
        return 'bg-indigo-900/60 text-indigo-300 border-indigo-700';
      case 'SAFETY_CHECK':
        return 'bg-amber-900/60 text-amber-300 border-amber-700';
      case 'EXECUTE':
        return 'bg-teal-900/60 text-teal-300 border-teal-700';
      case 'VERIFY':
        return 'bg-emerald-900/60 text-emerald-300 border-emerald-700';
      case 'ESCALATE':
        return 'bg-rose-900/60 text-rose-300 border-rose-700';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  const formatTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-lg h-full flex flex-col">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Incident Response Audit Timeline
        </span>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
          {timeline.length} Event(s)
        </span>
      </div>

      {timeline.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-slate-500 text-xs">
          <svg className="w-8 h-8 text-slate-600 mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Timeline is waiting. Trigger an investigation above to stream live graph events.
        </div>
      ) : (
        <div className="space-y-3 overflow-y-auto max-h-[580px] pr-1.5 custom-scrollbar">
          {timeline.map((event, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 hover:border-slate-700 transition-colors space-y-1.5"
            >
              <div className="flex items-center justify-between gap-2">
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase border ${getStageColor(
                    event.stage
                  )}`}
                >
                  {event.stage}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">
                  {formatTime(event.timestamp)}
                </span>
              </div>
              <div className="text-xs font-medium text-slate-200 leading-snug">
                {event.summary}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
