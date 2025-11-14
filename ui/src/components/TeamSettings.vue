<template>
  <v-card>
    <v-card-title>Team Details</v-card-title>
    <v-card-text>
      <!-- Target team size -->
      <div class="mb-6">
        <label class="text-subtitle-2 d-block mb-2">Target Team Size</label>
        <div class="d-flex align-center">
          <v-btn
            icon="mdi-minus"
            size="small"
            variant="outlined"
            :disabled="store.targetTeamSize <= 3"
            @click="decrementTeamSize"
          ></v-btn>

          <v-text-field
            v-model.number="store.targetTeamSize"
            type="number"
            min="3"
            density="compact"
            hide-details
            class="mx-4 team-size-input"
            variant="outlined"
          ></v-text-field>

          <v-btn
            icon="mdi-plus"
            size="small"
            variant="outlined"
            @click="incrementTeamSize"
          ></v-btn>
        </div>
        <div class="text-caption text-grey mt-1">
          Must be greater than 2
        </div>
      </div>

      <!-- Less than target setting -->
      <div class="mb-6">
        <label class="text-subtitle-2 d-block mb-2">
          If target size can't be met exactly
        </label>
        <v-select
          v-model="store.lessThanTarget"
          :items="sizeOptions"
          density="compact"
          variant="outlined"
        ></v-select>
        <div class="text-caption text-grey mt-1">
          Choose whether to make some teams slightly larger or smaller when the total number
          of participants can't be assigned evenly.
        </div>
      </div>

      <!-- Max time -->
      <div class="mb-6">
        <label class="text-subtitle-2 d-block mb-2">
          Maximum Search Time (seconds)
        </label>
        <v-text-field
          v-model.number="store.maxTime"
          type="number"
          min="1"
          density="compact"
          variant="outlined"
          suffix="seconds"
        ></v-text-field>
        <div class="text-caption text-grey mt-1">
          How long to search for the optimal solution. Longer times may find better solutions.
        </div>
      </div>

      <!-- Action buttons -->
      <div class="d-flex justify-space-between align-center">
        <v-btn
          color="error"
          variant="outlined"
          prepend-icon="mdi-refresh"
          :disabled="!canReset"
          @click="handleReset"
        >
          Reset
        </v-btn>

        <v-btn
          color="primary"
          size="large"
          prepend-icon="mdi-play"
          :disabled="!store.canRunAssignment"
          :loading="store.appState === AppState.RUNNING"
          @click="handleCreateTeams"
        >
          Create Teams
        </v-btn>
      </div>

      <!-- Error display -->
      <v-alert
        v-if="store.errorMessage"
        type="error"
        class="mt-4"
        closable
        @click:close="store.clearError()"
      >
        {{ store.errorMessage }}
      </v-alert>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTeamFormationStore } from '@/stores/teamFormation'
import { assignTeams } from '@/services/api'
import { AppState } from '@/types'

const store = useTeamFormationStore()

const sizeOptions = [
  { title: 'Make teams slightly larger', value: false },
  { title: 'Make teams slightly smaller', value: true }
]

const canReset = computed(() => {
  return store.results !== null || store.progressEvents.length > 0
})

function incrementTeamSize() {
  store.targetTeamSize++
}

function decrementTeamSize() {
  if (store.targetTeamSize > 3) {
    store.targetTeamSize--
  }
}

function handleReset() {
  if (confirm('This will clear the current team assignments and start over. Continue?')) {
    store.reset()
  }
}

async function handleCreateTeams() {
  // Validate first
  const validation = store.validateConstraints()
  if (!validation.valid) {
    store.setError(`Cannot create teams: ${validation.errors.join(', ')}`)
    return
  }

  // Clear any previous errors
  store.clearError()

  // Set state to running
  store.setState(AppState.RUNNING)

  // Build request
  const request = {
    participants: store.participants,
    constraints: store.constraints,
    target_team_size: store.targetTeamSize,
    less_than_target: store.lessThanTarget,
    max_time: store.maxTime
  }

  try {
    await assignTeams(request, {
      onProgress: (event) => {
        store.addProgressEvent(event)
      },
      onComplete: (event) => {
        store.setResults(event)
      },
      onError: (event) => {
        store.setError(event.message)
      },
      onConnectionError: (error) => {
        store.setError(`Connection error: ${error.message}`)
      }
    })
  } catch (error) {
    if (error instanceof Error) {
      store.setError(error.message)
    } else {
      store.setError('An unknown error occurred')
    }
  }
}
</script>

<style scoped>
.team-size-input {
  max-width: 100px;
  text-align: center;
}

:deep(.team-size-input input) {
  text-align: center;
}
</style>
