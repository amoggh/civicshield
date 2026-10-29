/**
 * Typed API client for CivicShield backend communication.
 */

import type {
  AgentStatusResponse,
  AutonomyMode,
  ClinicHealthResponse,
  DiagnosticReport,
  EvaluationReport,
  FaultStatusResponse,
  WorkflowResumeRequest,
  WorkflowRunResponse,
} from '../types/api';

const API_BASE = 'http://localhost:8000';

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!res.ok) {
      let errorMsg = `HTTP ${res.status} ${res.statusText}`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          errorMsg = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        } else if (errorJson.message) {
          errorMsg = errorJson.message;
        }
      } catch {
        // use default statusText
      }
      throw new ApiError(res.status, errorMsg);
    }

    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new Error(`Failed to reach CivicShield backend at ${url}. Is uvicorn running on port 8000?`);
  }
}

export const api = {
  // Clinic
  getClinicHealth: () => request<ClinicHealthResponse>('/clinic/health'),

  // Diagnostics
  getDiagnosticReport: () => request<DiagnosticReport>('/diagnostics/report'),

  // Simulator Faults
  getActiveFaults: () => request<FaultStatusResponse>('/simulator/faults'),
  injectFault: (faultType: string, params: Record<string, unknown> = {}) =>
    request<FaultStatusResponse>('/simulator/faults/inject', {
      method: 'POST',
      body: JSON.stringify({ fault_type: faultType, params }),
    }),
  resetFaults: () =>
    request<FaultStatusResponse>('/simulator/faults/reset', {
      method: 'POST',
    }),

  // Agent & LangGraph Workflow
  getAgentStatus: () => request<AgentStatusResponse>('/agent/status'),
  runWorkflow: (
    incidentDescription: string,
    autonomyMode: AutonomyMode = 'autonomous',
    forceFallback: boolean = false,
    maxAttempts: number = 3
  ) =>
    request<WorkflowRunResponse>('/workflow/run', {
      method: 'POST',
      body: JSON.stringify({
        incident_description: incidentDescription,
        autonomy_mode: autonomyMode,
        force_fallback: forceFallback,
        max_attempts: maxAttempts,
      }),
    }),
  resumeWorkflow: (req: WorkflowResumeRequest) =>
    request<WorkflowRunResponse>('/workflow/resume', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  // Evaluation & Benchmark
  getBenchmarkResults: () => request<EvaluationReport>('/evaluation/results'),
  runBenchmark: () =>
    request<EvaluationReport>('/evaluation/run', {
      method: 'POST',
    }),
};
