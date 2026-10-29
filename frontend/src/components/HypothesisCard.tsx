import React from 'react';
import { Sparkles, Brain } from 'lucide-react';
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
      <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-900/20 p-5 text-center">
        <div className="flex justify-center mb-2">
          <Brain className="h-6 w-6 text-zinc-600" />
        </div>
        <div className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1">
          Step 1: AI Diagnostic Investigation
        </div>
        <p className="text-xs text-zinc-500 max-w-sm mx-auto">
          Waiting for trigger. Select a fault scenario above and click &quot;Run AI Investigation&quot; to formulate a root cause hypothesis.
        </p>
      </div>
    );
  }

  const decision = recommendation?.decision_type || 'RECOVER';
  const confidence = recommendation ? Math.round(recommendation.confidence_score * 100) : 100;
  const source = recommendation?.source || 'GEMINI_LLM';

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-zinc-300" />
          <span className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
            Step 1 · Root Cause Hypothesis
          </span>
          <span
            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${decision === 'RECOVER'
                ? 'bg-zinc-800 text-zinc-200 border-zinc-700'
                : decision === 'ESCALATE'
                  ? 'bg-red-950/60 text-red-400 border-red-800/60'
                  : 'bg-zinc-800 text-zinc-400 border-zinc-700'
              }`}
          >
            {decision}
          </span>
        </div>
        <span className="text-[11px] text-zinc-400 font-mono">
          Model: {source} ({confidence}% conf)
        </span>
      </div>

      {/* Main Statement */}
      <div className="p-3.5 rounded-lg bg-zinc-950 border border-zinc-800/80">
        <div className="text-[11px] font-medium text-zinc-400 mb-1">Diagnosed Root Cause:</div>
        <div className="text-sm font-medium text-zinc-100 leading-relaxed">
          {hypothesis || recommendation?.hypothesis}
        </div>
      </div>

      {/* Rationale & Plan */}
      {recommendation?.rationale && (
        <div className="text-xs text-zinc-400 leading-relaxed space-y-1">
          <span className="text-zinc-500 font-medium">Investigation Evidence:</span>{' '}
          {recommendation.rationale}
        </div>
      )}

      {/* Proposed Recovery Action */}
      {recommendation?.recovery_action && (
        <div className="pt-2 border-t border-zinc-800/60 flex items-center justify-between text-xs">
          <span className="text-zinc-400">Proposed Action:</span>
          <code className="px-2 py-0.5 rounded bg-zinc-950 border border-zinc-800 text-zinc-200 font-mono text-[11px]">
            {recommendation.recovery_action}
          </code>
        </div>
      )}
    </div>
  );
};
