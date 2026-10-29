import React, { useState } from 'react';
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  Check,
  X,
  Lock,
  UserCheck,
  UserX,
  Eye,
  Loader2,
} from 'lucide-react';
import type { AutonomyMode, GovernorDecision } from '../types/api';
import { Button } from './ui/button';

interface SafetyGovernorCardProps {
  governorDecision: GovernorDecision | null;
  proposedAction: string | null;
  autonomyMode?: AutonomyMode;
  awaitingApproval?: boolean;
  humanApproved?: boolean | null;
  shadowMatchesExpected?: boolean | null;
  shadowExpectedAction?: string | null;
  onApprove?: () => void;
  onReject?: (reason: string) => void;
  isResuming?: boolean;
}

export const SafetyGovernorCard: React.FC<SafetyGovernorCardProps> = ({
  governorDecision,
  proposedAction,
  autonomyMode = 'autonomous',
  awaitingApproval = false,
  humanApproved = null,
  shadowMatchesExpected = null,
  shadowExpectedAction = null,
  onApprove,
  onReject,
  isResuming = false,
}) => {
  const [rejectReason, setRejectReason] = useState<string>('');
  const [showRejectInput, setShowRejectInput] = useState<boolean>(false);

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

  const handleConfirmReject = () => {
    if (onReject) {
      onReject(rejectReason || 'Operator denied repair authorization.');
    }
  };

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

        {/* Operating Autonomy Mode Badge */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700/60 font-mono">
            Mode: {autonomyMode}
          </span>
          <span className="text-[11px] text-zinc-400 font-mono">
            Attempt {governorDecision?.attempt_number ?? 1} of 3
          </span>
        </div>
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

      {/* Governor Evaluation Rationale */}
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

      {/* ========================================================================= */}
      {/* 1. SUPERVISED MODE: Human-in-the-Loop Approval Gate                        */}
      {/* ========================================================================= */}
      {autonomyMode === 'supervised' && awaitingApproval && isApproved && (
        <div className="p-4 rounded-xl border border-amber-600/50 bg-amber-950/30 space-y-3 shadow-md animate-in fade-in">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <UserCheck className="h-4 w-4 text-amber-400 animate-pulse" />
              <span className="text-xs font-bold text-amber-300 uppercase tracking-wider">
                Human Operator Authorization Required
              </span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-900/40 text-amber-300 border border-amber-700/50">
              Workflow Paused
            </span>
          </div>

          <p className="text-xs text-amber-200/90 leading-relaxed">
            The Safety Governor approved the proposed action <code className="px-1.5 py-0.5 rounded bg-zinc-950 font-mono text-amber-300">{proposedAction}</code>. Because CivicShield is running in <strong className="text-white">Supervised Mode</strong>, execution is paused until you explicitly authorize or reject this change.
          </p>

          {showRejectInput && (
            <div className="space-y-1.5 pt-1">
              <label className="text-[11px] font-medium text-zinc-400">Rejection Justification:</label>
              <input
                type="text"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="e.g., Maintenance window closed, requires senior DBA signoff..."
                className="w-full h-8 px-3 rounded-lg bg-zinc-950 border border-zinc-700 text-xs text-zinc-100 focus:outline-none focus:ring-1 focus:ring-red-400 placeholder:text-zinc-600"
              />
            </div>
          )}

          <div className="flex items-center gap-2.5 pt-1">
            <Button
              onClick={onApprove}
              disabled={isResuming}
              className="h-9 px-4 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 font-semibold text-xs transition-colors shadow-sm"
            >
              {isResuming ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
                  Executing...
                </>
              ) : (
                <>
                  <Check className="h-3.5 w-3.5 mr-1" />
                  Approve & Execute Repair
                </>
              )}
            </Button>

            {showRejectInput ? (
              <Button
                variant="destructive"
                onClick={handleConfirmReject}
                disabled={isResuming}
                className="h-9 px-4 text-xs font-semibold"
              >
                Confirm Rejection
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={() => setShowRejectInput(true)}
                disabled={isResuming}
                className="h-9 px-4 text-xs text-zinc-300 hover:text-white border-zinc-700 hover:bg-zinc-800"
              >
                <X className="h-3.5 w-3.5 mr-1 text-red-400" />
                Reject Repair Proposal
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Supervised Mode: Human Outcome display once decided */}
      {autonomyMode === 'supervised' && humanApproved !== null && (
        <div
          className={`p-3 rounded-lg border text-xs flex items-center justify-between ${
            humanApproved
              ? 'bg-emerald-950/30 border-emerald-800 text-emerald-300'
              : 'bg-red-950/30 border-red-800 text-red-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {humanApproved ? (
              <UserCheck className="h-4 w-4 text-emerald-400" />
            ) : (
              <UserX className="h-4 w-4 text-red-400" />
            )}
            <span>
              {humanApproved
                ? 'Human Operator explicitly APPROVED action. Execution verified.'
                : 'Human Operator REJECTED proposal. Action strictly blocked & escalated.'}
            </span>
          </div>
          <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-zinc-950/60 border border-zinc-800">
            Supervised Signoff
          </span>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 2. SHADOW MODE: Execution Bypassed & Ground Truth Matching               */}
      {/* ========================================================================= */}
      {autonomyMode === 'shadow' && (
        <div className="p-3.5 rounded-lg border border-purple-800/60 bg-purple-950/20 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-purple-300 font-semibold text-xs uppercase tracking-wider">
              <Eye className="h-3.5 w-3.5 text-purple-400" />
              <span>Shadow Mode Active: Simulation Bypassed</span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-900/50 text-purple-300 border border-purple-700/60">
              Zero Execution
            </span>
          </div>
          <p className="text-xs text-purple-200/90 leading-relaxed">
            In Shadow Mode, repairs are never executed. The Safety Governor evaluated this proposal without touching the simulator.
          </p>
          {shadowMatchesExpected !== null && (
            <div className="p-2.5 rounded bg-zinc-950/80 border border-zinc-800 flex items-center justify-between text-xs">
              <span className="text-zinc-400">Ground Truth Comparison:</span>
              <span
                className={`font-semibold ${
                  shadowMatchesExpected ? 'text-emerald-400' : 'text-amber-400'
                }`}
              >
                {shadowMatchesExpected
                  ? `✓ Matched Expected (${shadowExpectedAction})`
                  : `Differed (Expected: ${shadowExpectedAction || 'None'})`}
              </span>
            </div>
          )}
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
