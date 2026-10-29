import React from 'react';
import { CheckCircle2, AlertTriangle, CheckSquare } from 'lucide-react';
import type { VerificationResult } from '../types/api';

interface VerificationCardProps {
  verificationResult: VerificationResult | null;
  overallStatus: string;
}

export const VerificationCard: React.FC<VerificationCardProps> = ({
  verificationResult,
  overallStatus,
}) => {
  if (!verificationResult) {
    return (
      <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-900/20 p-5 text-center">
        <div className="flex justify-center mb-2">
          <CheckSquare className="h-6 w-6 text-zinc-600" />
        </div>
        <div className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1">
          Step 3: Post-Repair Verification Probe
        </div>
        <p className="text-xs text-zinc-500 max-w-sm mx-auto">
          Repairs are never assumed successful until verified by synthetic clinic booking transactions.
        </p>
      </div>
    );
  }

  const { verified, health_ok, database_ok, latency_ok, booking_test_ok, details } = verificationResult;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {verified ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          ) : (
            <AlertTriangle className="h-4 w-4 text-amber-400" />
          )}
          <span className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
            Step 3 · Verification & Recovery
          </span>
          <span
            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
              verified
                ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60'
                : overallStatus === 'ESCALATED'
                ? 'bg-amber-950/60 text-amber-400 border-amber-800/60'
                : 'bg-red-950/60 text-red-400 border-red-800/60'
            }`}
          >
            {verified ? 'RECOVERY VERIFIED' : overallStatus === 'ESCALATED' ? 'ESCALATED' : 'PROBE FAILED'}
          </span>
        </div>
        <span className="text-[11px] text-zinc-400 font-mono">
          Status: {overallStatus}
        </span>
      </div>

      {/* 4-Item Verification Checklist */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
        <div
          className={`p-2.5 rounded-lg border flex items-center justify-between ${
            health_ok
              ? 'bg-zinc-950/80 border-zinc-800 text-zinc-200'
              : 'bg-red-950/20 border-red-900/40 text-red-300'
          }`}
        >
          <span className="text-[11px] text-zinc-400">Service API</span>
          <span className={`font-semibold text-xs ${health_ok ? 'text-emerald-400' : 'text-red-400'}`}>
            {health_ok ? 'Pass' : 'Fail'}
          </span>
        </div>

        <div
          className={`p-2.5 rounded-lg border flex items-center justify-between ${
            database_ok
              ? 'bg-zinc-950/80 border-zinc-800 text-zinc-200'
              : 'bg-red-950/20 border-red-900/40 text-red-300'
          }`}
        >
          <span className="text-[11px] text-zinc-400">Database</span>
          <span className={`font-semibold text-xs ${database_ok ? 'text-emerald-400' : 'text-red-400'}`}>
            {database_ok ? 'Pass' : 'Fail'}
          </span>
        </div>

        <div
          className={`p-2.5 rounded-lg border flex items-center justify-between ${
            latency_ok
              ? 'bg-zinc-950/80 border-zinc-800 text-zinc-200'
              : 'bg-red-950/20 border-red-900/40 text-red-300'
          }`}
        >
          <span className="text-[11px] text-zinc-400">Latency SLA</span>
          <span className={`font-semibold text-xs ${latency_ok ? 'text-emerald-400' : 'text-red-400'}`}>
            {latency_ok ? 'Pass' : 'Fail'}
          </span>
        </div>

        <div
          className={`p-2.5 rounded-lg border flex items-center justify-between ${
            booking_test_ok
              ? 'bg-zinc-950/80 border-zinc-800 text-zinc-200'
              : 'bg-red-950/20 border-red-900/40 text-red-300'
          }`}
        >
          <span className="text-[11px] text-zinc-400">Booking Probe</span>
          <span className={`font-semibold text-xs ${booking_test_ok ? 'text-emerald-400' : 'text-red-400'}`}>
            {booking_test_ok ? 'Pass' : 'Fail'}
          </span>
        </div>
      </div>

      {/* Synthetic Booking Details */}
      {details && (
        <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800 text-xs text-zinc-400 flex items-center justify-between">
          <span className="truncate">
            <span className="text-zinc-500 font-medium">Probe Result:</span> {details}
          </span>
          <span className="text-[10px] font-mono text-zinc-500 shrink-0 ml-2">
            Synthetic Booking Verified
          </span>
        </div>
      )}
    </div>
  );
};
