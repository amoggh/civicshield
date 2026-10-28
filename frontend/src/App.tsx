/**
 * CivicShield — main App component (Phase 1: skeleton only).
 *
 * Shows a simple landing page to prove React + Tailwind are wired up.
 * The dashboard, incident timeline, and controls will be added in later phases.
 */

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-8">
      {/* Logo / Title */}
      <div className="text-center space-y-4">
        <h1 className="text-5xl font-bold tracking-tight">
          <span className="text-emerald-400">Civic</span>Shield
        </h1>
        <p className="text-slate-400 text-lg max-w-md mx-auto">
          Safety-governed agentic AI for simulated clinic incident response
        </p>
      </div>

      {/* Status card — will become the dashboard entry point */}
      <div className="mt-10 bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-sm shadow-lg">
        <div className="flex items-center gap-3 mb-3">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </span>
          <span className="text-sm font-medium text-slate-300">System Online</span>
        </div>
        <p className="text-xs text-slate-500">
          Backend API and frontend are connected. Ready for Phase 2.
        </p>
      </div>
    </div>
  );
}

export default App;
