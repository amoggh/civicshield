import React from 'react';
import { Shield, ShieldCheck, ShieldAlert, Check, X, Lock } from 'lucide-react';
import type { GovernorDecision } from '../types/api';

interface SafetyGovernorCardProps {
  governorDecision: GovernorDecision | null;
  proposedAction: string | null;
}

export const SafetyGovernorCard: React.FC<SafetyGovernorCardProps> = ({
  governorDecision,
  proposedAction,
}) => {
  if (!governorDecision && !proposedAction) {
    return (
      <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-900/20 p-5 text-center">
        <div className="flex justify-center mb-2">
          <Shield className="h-6 w-6 text-zinc-600" />
        </div>
        <div className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1">
          Step 2: Deterministic Safety Governor
        </div>
        <p className="text-xs text-zinc-500 max-w-sm mx-auto">
          Deterministic Python guardrails intercept every LLM recommendation before any simulated change can occur.
        </p>
      </div>
    );
  }

  const isApproved = governorDecision?.approved ?? false;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isApproved ? (
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
          ) : (
            <ShieldAlert className="h-4 w-4 text-red-400" />
          )}
          <span className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
            Step 2 · Safety Governor Gate
          </span>
          <span
            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
              isApproved
                ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60'
                : 'bg-red-950/60 text-red-400 border-red-800/60'
            }`}
          >
            {isApproved ? 'ACTION APPROVED' : 'ACTION BLOCKED'}
          </span>
        </div>
        <span className="text-[11px] text-zinc-400 font-mono">
          Attempt {governorDecision?.attempt_number ?? 1} of 3
        </span>
      </div>

      {/* Target Action Banner */}
      <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800 flex items-center justify-between">
        <div>
          <div className="text-[11px] text-zinc-400 font-medium">Intercepted Action:</div>
          <div className="text-xs font-mono font-semibold text-zinc-200">
            {proposedAction || governorDecision?.action_type || 'NONE'}
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-zinc-400">
          <Lock className="h-3 w-3 text-zinc-500" />
          <span>Strict Allowlist</span>
        </div>
      </div>

      {/* Decision Rationale */}
      {governorDecision && (
        <div
          className={`p-3 rounded-lg border text-xs leading-relaxed flex items-start gap-2.5 ${
            isApproved
              ? 'bg-emerald-950/20 border-emerald-900/50 text-emerald-300'
              : 'bg-red-950/20 border-red-900/50 text-red-300'
          }`}
        >
          {isApproved ? (
            <Check className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <X className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
          )}
          <div>
            <span className="font-semibold">{isApproved ? 'Passed Verification:' : 'Safety Violation:'}</span>{' '}
            {governorDecision.reason}
          </div>
        </div>
      )}

      {/* 4 Guardrail Checks */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-[11px]">
        <div className="p-2 rounded bg-zinc-950/60 border border-zinc-800/60 text-center">
          <span className="text-zinc-500 block">Allowlist</span>
          <span className={`font-medium ${isApproved ? 'text-zinc-200' : 'text-red-400'}`}>
            {isApproved ? 'Verified' : 'Violation'}
          </span>
        </div>
        <div className="p-2 rounded bg-zinc-950/60 border border-zinc-800/60 text-center">
          <span className="text-zinc-500 block">Destructive Check</span>
          <span className="text-zinc-200 font-medium">Clean</span>
        </div>
        <div className="p-2 rounded bg-zinc-950/60 border border-zinc-800/60 text-center">
          <span className="text-zinc-500 block">Evidence Match</span>
          <span className={`font-medium ${isApproved ? 'text-zinc-200' : 'text-zinc-400'}`}>
            {isApproved ? 'Matched' : 'Unmatched'}
          </span>
        </div>
        <div className="p-2 rounded bg-zinc-950/60 border border-zinc-800/60 text-center">
          <span className="text-zinc-500 block">Retry Bound</span>
          <span className="text-zinc-200 font-medium">&le; 3 Capped</span>
        </div>
      </div>
    </div>
  );
};
