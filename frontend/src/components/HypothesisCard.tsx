import React from 'react';
import type { PlannerRecommendation } from '../types/api';

interface HypothesisCardProps {
  recommendation: PlannerRecommendation | null;
  hypothesis: string;
}

export const HypothesisCard: React.FC<HypothesisCardProps> = ({
  recommendation,
  hypothesis,
}) => {
  if (!recommendation && !hypothesis) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 text-slate-500 text-sm">
        <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
          AI Investigator & Hypothesis
        </div>
        <p>No investigation run yet. Click &quot;Run Investigation&quot; to formulate a hypothesis from live diagnostics.</p>
      </div>
    );
  }

  const decision = recommendation?.decision_type || 'NO_ACTION';
  const confidence = recommendation ? Math.round(recommendation.confidence_score * 100) : 100;
  const source = recommendation?.source || 'STANDBY';

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            AI Hypothesis & Plan
          </span>
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase border ${
              decision === 'RECOVER'
                ? 'bg-blue-950 text-blue-400 border-blue-800'
                : decision === 'ESCALATE'
                ? 'bg-rose-950 text-rose-400 border-rose-800'
                : 'bg-emerald-950 text-emerald-400 border-emerald-800'
            }`}
          >
            {decision}
          </span>
        </div>
        <span className="text-[10px] text-slate-400 font-mono bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
          Source: {source}
        </span>
      </div>

      {/* Hypothesis Statement */}
      <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80">
        <div className="text-xs text-slate-400 font-medium mb-1">Root Cause Hypothesis:</div>
        <div className="text-sm font-semibold text-slate-100 leading-relaxed">
          {hypothesis || recommendation?.hypothesis}
        </div>
      </div>

      {/* Rationale */}
      {recommendation?.rationale && (
        <div className="text-xs text-slate-400 space-y-1">
          <span className="font-semibold text-slate-300">Diagnostic Rationale: </span>
          <span>{recommendation.rationale}</span>
        </div>
      )}

      {/* Supporting Evidence Tags */}
      {recommendation?.supporting_evidence && recommendation.supporting_evidence.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="text-[11px] text-slate-500">Evidence Tags:</span>
          {recommendation.supporting_evidence.map((tag, idx) => (
            <span
              key={idx}
              className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Confidence Meter */}
      <div className="space-y-1.5 pt-2 border-t border-slate-800/60">
        <div className="flex justify-between text-xs text-slate-400">
          <span>Confidence Score</span>
          <span className="font-bold text-slate-200">{confidence}%</span>
        </div>
        <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
          <div
            className={`h-full transition-all duration-500 rounded-full ${
              confidence > 80 ? 'bg-emerald-500' : confidence > 50 ? 'bg-blue-500' : 'bg-amber-500'
            }`}
            style={{ width: `${confidence}%` }}
          />
        </div>
      </div>
    </div>
  );
};
