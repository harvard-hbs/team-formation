import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Participant,
  Constraint,
  ConstraintPreset,
  ProgressEvent,
  CompleteEvent,
  AppState,
  CohortInfo,
  TeamSummary,
  ValidationResult
} from '@/types'
import { AppState as AppStateEnum } from '@/types'

export const useTeamFormationStore = defineStore('teamFormation', () => {
  // ===== State =====

  // Participants data
  const participants = ref<Participant[]>([])
  const originalParticipants = ref<Participant[]>([]) // Keep original for reset

  // Constraints
  const constraints = ref<Constraint[]>([])

  // Team settings
  const targetTeamSize = ref<number>(7)
  const lessThanTarget = ref<boolean>(true)
  const maxTime = ref<number>(60)

  // Application state
  const appState = ref<AppState>(AppStateEnum.IDLE)

  // Progress tracking
  const progressEvents = ref<ProgressEvent[]>([])
  const currentProgress = ref<ProgressEvent | null>(null)

  // Results
  const results = ref<Participant[] | null>(null)
  const stats = ref<any>(null)

  // Errors
  const errorMessage = ref<string | null>(null)

  // Presets stored in localStorage
  const presets = ref<ConstraintPreset[]>([])

  // ===== Computed =====

  // Get available attribute columns from participants
  const availableAttributes = computed(() => {
    if (participants.value.length === 0) return []

    // Get all unique keys from all participants
    const allKeys = new Set<string>()
    participants.value.forEach(p => {
      Object.keys(p).forEach(key => {
        if (key !== 'team_number') { // Exclude team assignment column
          allKeys.add(key)
        }
      })
    })

    return Array.from(allKeys).sort()
  })

  // Check if we have participants loaded
  const hasParticipants = computed(() => participants.value.length > 0)

  // Check if we have constraints
  const hasConstraints = computed(() => constraints.value.length > 0)

  // Check if ready to run
  const canRunAssignment = computed(() => {
    return hasParticipants.value &&
           targetTeamSize.value > 2 &&
           appState.value !== AppStateEnum.RUNNING
  })

  // Get cohort information
  const cohortInfo = computed<CohortInfo>(() => {
    const numAssigned = participants.value.filter(p => p.team_number !== undefined).length
    const numTeams = results.value
      ? new Set(results.value.map(p => p.team_number)).size
      : undefined

    return {
      num_participants: participants.value.length,
      num_assigned: numAssigned,
      num_teams: numTeams
    }
  })

  // Group participants by team
  const teamSummaries = computed<TeamSummary[]>(() => {
    if (!results.value) return []

    const teams = new Map<number, Participant[]>()
    results.value.forEach(p => {
      if (p.team_number !== undefined) {
        if (!teams.has(p.team_number)) {
          teams.set(p.team_number, [])
        }
        teams.get(p.team_number)!.push(p)
      }
    })

    return Array.from(teams.entries())
      .map(([team_number, members]) => ({
        team_number,
        member_count: members.length,
        members
      }))
      .sort((a, b) => a.team_number - b.team_number)
  })

  // ===== Actions =====

  // Load participants from CSV data
  function loadParticipants(data: Participant[]) {
    participants.value = data
    originalParticipants.value = JSON.parse(JSON.stringify(data))
    results.value = null
    stats.value = null
    progressEvents.value = []
    appState.value = AppStateEnum.READY
  }

  // Add a new constraint
  function addConstraint(constraint: Constraint) {
    constraints.value.push(constraint)
  }

  // Update a constraint
  function updateConstraint(index: number, constraint: Constraint) {
    if (index >= 0 && index < constraints.value.length) {
      constraints.value[index] = constraint
    }
  }

  // Remove a constraint
  function removeConstraint(index: number) {
    if (index >= 0 && index < constraints.value.length) {
      constraints.value.splice(index, 1)
    }
  }

  // Validate constraints against available attributes
  function validateConstraints(): ValidationResult {
    const errors: string[] = []
    const warnings: string[] = []

    constraints.value.forEach((constraint, index) => {
      // Check if attribute exists
      if (!availableAttributes.value.includes(constraint.attribute)) {
        errors.push(`Constraint ${index + 1}: Attribute "${constraint.attribute}" not found in participant data`)
      }

      // Check weight is positive
      if (constraint.weight <= 0) {
        errors.push(`Constraint ${index + 1}: Weight must be greater than 0`)
      }
    })

    // Warnings
    if (targetTeamSize.value <= 2) {
      errors.push('Target team size must be greater than 2')
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    }
  }

  // Update progress
  function addProgressEvent(event: ProgressEvent) {
    progressEvents.value.push(event)
    currentProgress.value = event
  }

  // Set results
  function setResults(data: CompleteEvent) {
    results.value = data.participants
    stats.value = data.stats
    appState.value = AppStateEnum.COMPLETE

    // Update participants with team assignments
    participants.value = data.participants
  }

  // Set error
  function setError(message: string) {
    errorMessage.value = message
    appState.value = AppStateEnum.ERROR
  }

  // Clear error
  function clearError() {
    errorMessage.value = null
  }

  // Set app state
  function setState(state: AppState) {
    appState.value = state
  }

  // Reset to ready state (keep participants and constraints)
  function reset() {
    progressEvents.value = []
    currentProgress.value = null
    results.value = null
    stats.value = null
    errorMessage.value = null
    participants.value = JSON.parse(JSON.stringify(originalParticipants.value))
    appState.value = hasParticipants.value ? AppStateEnum.READY : AppStateEnum.IDLE
  }

  // Clear all data
  function clearAll() {
    participants.value = []
    originalParticipants.value = []
    constraints.value = []
    progressEvents.value = []
    currentProgress.value = null
    results.value = null
    stats.value = null
    errorMessage.value = null
    targetTeamSize.value = 7
    lessThanTarget.value = true
    maxTime.value = 60
    appState.value = AppStateEnum.IDLE
  }

  // ===== Presets Management =====

  // Load presets from localStorage
  function loadPresets() {
    try {
      const stored = localStorage.getItem('team-formation-presets')
      if (stored) {
        presets.value = JSON.parse(stored)
      }
    } catch (e) {
      console.error('Failed to load presets:', e)
    }
  }

  // Save preset
  function savePreset(name: string, description?: string) {
    const preset: ConstraintPreset = {
      name,
      description,
      constraints: JSON.parse(JSON.stringify(constraints.value)),
      target_team_size: targetTeamSize.value,
      less_than_target: lessThanTarget.value,
      max_time: maxTime.value,
      created_at: new Date().toISOString()
    }

    presets.value.push(preset)
    localStorage.setItem('team-formation-presets', JSON.stringify(presets.value))
  }

  // Load preset
  function loadPreset(index: number) {
    if (index >= 0 && index < presets.value.length) {
      const preset = presets.value[index]
      constraints.value = JSON.parse(JSON.stringify(preset.constraints))
      targetTeamSize.value = preset.target_team_size
      lessThanTarget.value = preset.less_than_target
      maxTime.value = preset.max_time
    }
  }

  // Delete preset
  function deletePreset(index: number) {
    if (index >= 0 && index < presets.value.length) {
      presets.value.splice(index, 1)
      localStorage.setItem('team-formation-presets', JSON.stringify(presets.value))
    }
  }

  // Initialize presets on store creation
  loadPresets()

  return {
    // State
    participants,
    constraints,
    targetTeamSize,
    lessThanTarget,
    maxTime,
    appState,
    progressEvents,
    currentProgress,
    results,
    stats,
    errorMessage,
    presets,

    // Computed
    availableAttributes,
    hasParticipants,
    hasConstraints,
    canRunAssignment,
    cohortInfo,
    teamSummaries,

    // Actions
    loadParticipants,
    addConstraint,
    updateConstraint,
    removeConstraint,
    validateConstraints,
    addProgressEvent,
    setResults,
    setError,
    clearError,
    setState,
    reset,
    clearAll,
    savePreset,
    loadPreset,
    deletePreset
  }
})
