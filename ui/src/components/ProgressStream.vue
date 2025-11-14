<template>
  <v-card v-if="store.appState === AppState.RUNNING || store.progressEvents.length > 0">
    <v-card-title class="d-flex align-center">
      <v-icon class="mr-2">mdi-progress-clock</v-icon>
      Optimization Progress
    </v-card-title>

    <v-card-text>
      <!-- Current progress summary -->
      <div v-if="store.currentProgress" class="mb-4">
        <v-row dense>
          <v-col cols="6" sm="3">
            <div class="text-caption text-grey">Solutions Found</div>
            <div class="text-h6">{{ store.currentProgress.solution_count }}</div>
          </v-col>

          <v-col cols="6" sm="3">
            <div class="text-caption text-grey">Objective Value</div>
            <div class="text-h6">{{ store.currentProgress.objective_value.toFixed(2) }}</div>
          </v-col>

          <v-col cols="6" sm="3">
            <div class="text-caption text-grey">Time Elapsed</div>
            <div class="text-h6">{{ store.currentProgress.wall_time.toFixed(1) }}s</div>
          </v-col>

          <v-col cols="6" sm="3">
            <div class="text-caption text-grey">Conflicts</div>
            <div class="text-h6">{{ store.currentProgress.num_conflicts }}</div>
          </v-col>
        </v-row>

        <!-- Progress bar for time -->
        <v-progress-linear
          :model-value="timeProgress"
          color="primary"
          height="8"
          class="mt-4"
        >
          <template v-slot:default>
            <span class="text-caption">{{ Math.round(timeProgress) }}%</span>
          </template>
        </v-progress-linear>
      </div>

      <!-- Animated running indicator -->
      <v-alert
        v-if="store.appState === AppState.RUNNING"
        type="info"
        variant="tonal"
        class="mb-4"
      >
        <div class="d-flex align-center">
          <v-progress-circular
            indeterminate
            size="20"
            width="2"
            class="mr-2"
          ></v-progress-circular>
          <span>Searching for optimal team assignments...</span>
        </div>
      </v-alert>

      <!-- Progress log -->
      <div v-if="store.progressEvents.length > 0">
        <v-divider class="mb-2"></v-divider>
        <div class="text-subtitle-2 mb-2">Progress Log</div>

        <v-list density="compact" class="progress-log">
          <v-list-item
            v-for="(event, index) in recentEvents"
            :key="index"
            class="text-caption"
          >
            <template v-slot:prepend>
              <v-icon size="small" color="success">mdi-check-circle</v-icon>
            </template>

            <v-list-item-title class="text-caption">
              {{ event.message }}
            </v-list-item-title>
          </v-list-item>
        </v-list>

        <div v-if="store.progressEvents.length > maxDisplayEvents" class="text-caption text-grey text-center mt-2">
          Showing last {{ maxDisplayEvents }} of {{ store.progressEvents.length }} updates
        </div>
      </div>

      <!-- Completion message -->
      <v-alert
        v-if="store.appState === AppState.COMPLETE && store.stats"
        type="success"
        class="mt-4"
      >
        <div class="d-flex align-center">
          <v-icon class="mr-2">mdi-check-circle</v-icon>
          <div>
            <div class="font-weight-bold">Team assignment complete!</div>
            <div class="text-caption">
              Found {{ store.stats.solution_count }} solutions in {{ store.stats.wall_time.toFixed(2) }}s.
              Created {{ store.stats.num_teams }} teams for {{ store.stats.num_participants }} participants.
            </div>
          </div>
        </div>
      </v-alert>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTeamFormationStore } from '@/stores/teamFormation'
import { AppState } from '@/types'

const store = useTeamFormationStore()

const maxDisplayEvents = 10

// Calculate time progress as percentage of max_time
const timeProgress = computed(() => {
  if (!store.currentProgress) return 0
  return Math.min((store.currentProgress.wall_time / store.maxTime) * 100, 100)
})

// Get recent events (last N)
const recentEvents = computed(() => {
  const events = [...store.progressEvents]
  return events.slice(-maxDisplayEvents).reverse()
})
</script>

<style scoped>
.progress-log {
  max-height: 250px;
  overflow-y: auto;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 4px;
}
</style>
