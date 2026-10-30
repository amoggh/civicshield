/**
 * TypeScript type definitions mirroring backend Pydantic models.
 */

export type ServiceStatus = 'healthy' | 'degraded' | 'down';

export interface ClinicHealthResponse {
  status: ServiceStatus;
  message: string;
  active_doctors: number;
  pending_appointments: number;
  timestamp: string;
}

export interface ServiceHealthEvidence {
  status: string;
  is_healthy: boolean;
  active_doctors: number;
  pending_appointments: number;
  message: string;
  observed_at: string;
}

export interface DatabaseEvidence {
  is_reachable: boolean;
  host: string;
  port: number;
  status_code: string;
  error_detail: string | null;
  response_time_ms: number;
  observed_at: string;
}

export interface ConfigDiffItem {
  key: string;
  baseline_value: unknown;
  current_value: unknown;
  is_divergent: boolean;
}

export interface ConfigEvidence {
  has_divergence: boolean;
  divergent_keys: string[];
  diffs: ConfigDiffItem[];
  observed_at: string;
}

export interface LatencyEvidence {
  sample_latencies_ms: number[];
  avg_latency_ms: number;
  threshold_ms: number;
  sla_violated: boolean;
  observed_at: string;
}

export interface LogEntry {
  timestamp: string;
  event: string;
  detail: string;
  service_status: string;
  is_error: boolean;
}

export interface LogEvidence {
  total_logs: number;
  error_count: number;
  has_errors: boolean;
  recent_entries: LogEntry[];
  observed_at: string;
}

export interface DiagnosticReport {
  service_health: ServiceHealthEvidence;
  database: DatabaseEvidence;
  configuration: ConfigEvidence;
  latency: LatencyEvidence;
  logs: LogEvidence;
  generated_at: string;
}

export interface FaultStatusResponse {
  active_faults: string[];
  details: Record<string, unknown>;
  timestamp: string;
}

export interface PlannerRecommendation {
  decision_type: 'INVESTIGATE' | 'RECOVER' | 'ESCALATE' | 'NO_ACTION';
  diagnostic_tool: string | null;
  recovery_action: string | null;
  parameters: Record<string, unknown>;
  hypothesis: string;
  rationale: string;
  supporting_evidence: string[];
  confidence_score: number;
  source: string;
  generated_at: string;
}

export interface ActionProposal {
  action_type: string;
  parameters: Record<string, unknown>;
  rationale: string;
  supporting_evidence: string[];
  attempt_number: number;
}

export interface GovernorDecision {
  approved: boolean;
  action_type: string;
  attempt_number: number;
  reason: string;
  requires_human_escalation: boolean;
  timestamp: string;
}

export interface ExecutionResult {
  executed: boolean;
  action_type: string;
  message: string;
  timestamp: string;
}

export interface VerificationResult {
  verified: boolean;
  health_ok: boolean;
  database_ok: boolean;
  latency_ok: boolean;
  booking_test_ok: boolean;
  details: string;
  timestamp: string;
}

export type AutonomyMode = 'shadow' | 'supervised' | 'autonomous';

export interface DiagnosticAnalysis {
  suspected_component: string;
  failure_mode: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  hypothesis: string;
  evidence_summary: string[];
  confidence_score: number;
  recommend_recovery: boolean;
  source: string;
  analyzed_at: string;
}

export interface ExecutionEvent {
  event_id: string;
  run_id: string;
  seq: number;
  timestamp: string;
  node: string;
  agent_id: string;
  agent_type: 'ai_agent' | 'deterministic_guardrail' | 'deterministic_tool' | 'workflow_controller' | 'human_operator' | string;
  event_type: 'node_start' | 'node_complete' | 'agent_handoff' | 'tool_call' | 'safety_evaluation' | 'human_review' | 'workflow_escalate' | string;
  status: 'success' | 'failed' | 'blocked' | 'paused' | 'escalated' | string;
  input_summary: string;
  output_summary: string;
  structured_payload: Record<string, unknown>;
  handoff_to: string | null;
  duration_ms: number | null;
  error_detail: string | null;
}

export interface WorkflowTimelineEvent {
  timestamp: string;
  stage: 'INTAKE' | 'DIAGNOSE' | 'ANALYZE' | 'PLAN' | 'SAFETY_CHECK' | 'EXECUTE' | 'VERIFY' | 'ESCALATE' | 'SHADOW_CHECK' | 'SUPERVISED_GATE' | 'SUPERVISED_APPROVAL' | 'SUPERVISED_REJECTION' | string;
  summary: string;
  details: Record<string, unknown>;
}

export interface WorkflowRunResponse {
  status: 'SUCCESS' | 'ESCALATED' | 'RETRYING' | 'DIAGNOSING' | 'COMPLETED' | 'SHADOW_EVALUATED' | 'AWAITING_APPROVAL';
  autonomy_mode?: AutonomyMode;
  incident_description: string;
  attempt_count: number;
  hypothesis: string;
  diagnostic_analysis?: DiagnosticAnalysis | null;
  planner_recommendation: PlannerRecommendation | null;
  proposed_action?: ActionProposal | null;
  governor_decision: GovernorDecision | null;
  execution_result: ExecutionResult | null;
  verification_result: VerificationResult | null;
  timeline: WorkflowTimelineEvent[];
  events?: ExecutionEvent[];
  completed_at: string;
  awaiting_approval?: boolean;
  human_approved?: boolean | null;
  shadow_matches_expected?: boolean | null;
  shadow_expected_action?: string | null;
}

export interface WorkflowResumeRequest {
  approved: boolean;
  rejection_reason?: string | null;
  paused_state: Record<string, unknown>;
}

export interface AgentStatusResponse {
  has_api_key: boolean;
  model_name: string;
  active_mode: string;
  available_diagnostic_tools: string[];
  allowed_recovery_actions: string[];
}

export interface RunResult {
  scenario: string;
  system: string;
  recovered: boolean;
  root_cause_correct: boolean;
  unsafe_rejected: boolean;
  attempts_used: number;
  unnecessary_attempts: number;
  execution_time_ms: number;
  details: string;
}

export interface SystemBenchmarkMetrics {
  system_name: string;
  total_scenarios: number;
  recovery_success_rate: number;
  root_cause_accuracy: number;
  unsafe_action_rejection_rate: number;
  total_unnecessary_attempts: number;
  avg_attempts_to_recover: number;
}

export interface EvaluationReport {
  generated_at: string;
  sample_size: number;
  limitations: string;
  civicshield_metrics: SystemBenchmarkMetrics;
  baseline_metrics: SystemBenchmarkMetrics;
  scenario_runs: RunResult[];
}
