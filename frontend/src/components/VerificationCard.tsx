import React from 'react';
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
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 text-slate-500 text-sm">
        <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
          Post-Repair Verification Probe
        </div>
        <p>No verification performed yet. Repairs must pass functional probes before declaring recovery.</p>
      </div>
    );
  }

  const { verified, health_ok, database_ok, latency_ok, booking_test_ok, details } = verificationResult;

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-lg">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Post-Repair Verification
        </span>
        <span
          className={`text-[10px] font-bold px-2.5 py-1 rounded-md uppercase border ${
            verified
              ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
              : 'bg-rose-950 text-rose-400 border-rose-800'
          }`}
        >
          {verified ? 'RECOVERY VERIFIED' : overallStatus === 'ESCALATED' ? 'ESCALATED' : 'VERIFICATION FAILED'}
        </span>
      </div>

      {/* 4-Item Verification Checklist */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div
          className={`p-2.5 rounded-xl border flex items-center justify-between ${
            health_ok ? 'bg-slate-950/80 border-emerald-900/50 text-slate-200' : 'bg-rose-950/20 border-rose-900/50 text-rose-300'
          }`}
        >
          <span>Service Health</span>
          <span className={`font-bold ${health_ok ? 'text-emerald-400' : 'text-rose-400'}`}>
            {health_ok ? '✓ PASS' : '✕ FAIL'}
          </span>
        </div>

        <div
          className={`p-2.5 rounded-xl border flex items-center justify-between ${
            database_ok ? 'bg-slate-950/80 border-emerald-900/50 text-slate-200' : 'bg-rose-950/20 border-rose-900/50 text-rose-300'
          }`}
        >
          <span>Database Socket</span>
          <span className={`font-bold ${database_ok ? 'text-emerald-400' : 'text-rose-400'}`}>
            {database_ok ? '✓ PASS' : '✕ FAIL'}
          </span>
        </div>

        <div
          className={`p-2.5 rounded-xl border flex items-center justify-between ${
            latency_ok ? 'bg-slate-950/80 border-emerald-900/50 text-slate-200' : 'bg-rose-950/20 border-rose-900/50 text-rose-300'
          }`}
        >
          <span>Latency SLA</span>
          <span className={`font-bold ${latency_ok ? 'text-emerald-400' : 'text-rose-400'}`}>
            {latency_ok ? '✓ PASS' : '✕ FAIL'}
          </span>
        </div>

        <div
          className={`p-2.5 rounded-xl border flex items-center justify-between ${
            booking_test_ok ? 'bg-slate-950/80 border-emerald-900/50 text-slate-200' : 'bg-rose-950/20 border-rose-900/50 text-rose-300'
          }`}
        >
          <span>Synthetic Booking</span>
          <span className={`font-bold ${booking_test_ok ? 'text-emerald-400' : 'text-rose-400'}`}>
            {booking_test_ok ? '✓ PASS' : '✕ FAIL'}
          </span>
        </div>
      </div>

      {/* Details Description */}
      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400 leading-relaxed">
        {details}
      </div>
    </div>
  );
};
