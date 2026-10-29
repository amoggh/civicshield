import React from 'react';
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
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 text-slate-500 text-sm">
        <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
          Deterministic Safety Governor
        </div>
        <p>No action proposed yet. Safety checks run automatically before any repair executes.</p>
      </div>
    );
  }

  const isApproved = governorDecision?.approved ?? false;

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-lg">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Safety Governor & Allowlist
        </span>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
          Rule: Strict Allowlist & Bounded Retries
        </span>
      </div>

      {/* Proposed Action Display */}
      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
        <div>
          <div className="text-[11px] text-slate-400 font-medium">Proposed Action:</div>
          <div className="text-sm font-mono font-bold text-slate-200">
            {proposedAction || governorDecision?.action_type || 'NONE'}
          </div>
        </div>
        <span className="text-[10px] font-semibold px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
          Attempt #{governorDecision?.attempt_number ?? 1} of 3
        </span>
      </div>

      {/* Governor Evaluation Banner */}
      {governorDecision && (
        <div
          className={`p-3.5 rounded-xl border flex items-start gap-3 ${
            isApproved
              ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
              : 'bg-rose-950/40 border-rose-800 text-rose-300'
          }`}
        >
          <div
            className={`mt-0.5 h-4 w-4 rounded-full flex items-center justify-center shrink-0 ${
              isApproved ? 'bg-emerald-500 text-slate-950' : 'bg-rose-500 text-white'
            }`}
          >
            {isApproved ? '✓' : '✕'}
          </div>
          <div className="space-y-1">
            <div className="text-xs font-bold uppercase tracking-wider">
              {isApproved ? 'SAFETY GATE: APPROVED' : 'SAFETY GATE: REJECTED & BLOCKED'}
            </div>
            <div className="text-xs leading-relaxed opacity-90">{governorDecision.reason}</div>
            {governorDecision.requires_human_escalation && (
              <div className="text-[11px] font-semibold text-rose-400 pt-1">
                ⚠️ Requires Mandatory Human Administrator Escalation
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
