// Participant interface - flexible schema with any attributes
export interface Participant {
  [key: string]: any
  team_number?: number
}

// Constraint types supported by the API
export type ConstraintType = 'cluster' | 'cluster_numeric' | 'different' | 'diversify'

// Constraint interface matching API spec
export interface Constraint {
  attribute: string
  type: ConstraintType
  weight: number
}

// Team assignment request payload
export interface TeamAssignmentRequest {
  participants: Participant[]
  constraints: Constraint[]
  target_team_size: number
  less_than_target?: boolean
  max_time?: number
}

// Progress event data from SSE stream
export interface ProgressEvent {
  event_type: 'progress'
  solution_count: number
  objective_value: number
  wall_time: number
  num_conflicts: number
  message: string
}

// Complete event data from SSE stream
export interface CompleteEvent {
  participants: Participant[]
  stats: {
    solution_count: number
    wall_time: number
    num_teams: number
    num_participants: number
  }
}

// Error event data from SSE stream
export interface ErrorEvent {
  event_type: 'error'
  message: string
}

// Union type for all SSE events
export type SSEEvent = ProgressEvent | CompleteEvent | ErrorEvent

// Application state enum
export enum AppState {
  IDLE = 'idle',
  UPLOADING = 'uploading',
  READY = 'ready',
  RUNNING = 'running',
  COMPLETE = 'complete',
  ERROR = 'error'
}

// Constraint preset for saving/loading
export interface ConstraintPreset {
  name: string
  description?: string
  constraints: Constraint[]
  target_team_size: number
  less_than_target: boolean
  max_time: number
  created_at: string
}

// Team summary for visualization
export interface TeamSummary {
  team_number: number
  member_count: number
  members: Participant[]
}

// Validation result
export interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
}

// Cohort information
export interface CohortInfo {
  cohort_id?: string
  waves?: string
  num_participants: number
  num_assigned: number
  num_teams?: number
  last_updated?: string
}

// Different constraint evaluation for a single team
export interface DifferentConstraintTeamEval {
  team_number: number
  team_size: number
  missed: number  // team_size - unique_values = number sharing a value
}

// Different constraint evaluation for all teams
export interface DifferentConstraintEvaluation {
  attribute: string
  teams: DifferentConstraintTeamEval[]
}
