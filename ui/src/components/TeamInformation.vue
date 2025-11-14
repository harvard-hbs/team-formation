<template>
  <v-card class="mb-4">
    <v-card-title>Team Information</v-card-title>
    <v-card-text>
      <v-row dense>
        <v-col cols="12" md="6">
          <div class="info-item">
            <span class="text-subtitle-2 text-grey">Number of Participants:</span>
            <span class="text-h6 ml-2">
              {{ store.cohortInfo.num_participants }}
              <span v-if="store.cohortInfo.num_assigned > 0" class="text-caption">
                ({{ store.cohortInfo.num_assigned }} assigned to a team)
              </span>
            </span>
          </div>
        </v-col>

        <v-col cols="12" md="6" v-if="store.cohortInfo.num_teams">
          <div class="info-item">
            <span class="text-subtitle-2 text-grey">Number of Teams:</span>
            <span class="text-h6 ml-2">{{ store.cohortInfo.num_teams }}</span>
          </div>
        </v-col>

        <v-col cols="12" v-if="store.stats">
          <v-divider class="my-2"></v-divider>
          <div class="info-item">
            <span class="text-subtitle-2 text-grey">Last Updated:</span>
            <span class="text-body-1 ml-2">{{ formattedUpdateTime }}</span>
          </div>
          <div class="info-item mt-2">
            <span class="text-subtitle-2 text-grey">Solution Stats:</span>
            <span class="text-body-2 ml-2">
              {{ store.stats.solution_count }} solutions found in {{ store.stats.wall_time.toFixed(2) }}s
            </span>
          </div>
        </v-col>
      </v-row>

      <!-- Status indicator -->
      <v-row dense class="mt-2">
        <v-col cols="12">
          <v-chip
            :color="statusColor"
            :prepend-icon="statusIcon"
            size="small"
          >
            {{ statusText }}
          </v-chip>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTeamFormationStore } from '@/stores/teamFormation'
import { AppState } from '@/types'

const store = useTeamFormationStore()

const formattedUpdateTime = computed(() => {
  return new Date().toLocaleString()
})

const statusColor = computed(() => {
  switch (store.appState) {
    case AppState.IDLE:
      return 'grey'
    case AppState.READY:
      return 'info'
    case AppState.RUNNING:
      return 'warning'
    case AppState.COMPLETE:
      return 'success'
    case AppState.ERROR:
      return 'error'
    default:
      return 'grey'
  }
})

const statusIcon = computed(() => {
  switch (store.appState) {
    case AppState.IDLE:
      return 'mdi-sleep'
    case AppState.READY:
      return 'mdi-check-circle'
    case AppState.RUNNING:
      return 'mdi-loading mdi-spin'
    case AppState.COMPLETE:
      return 'mdi-check-circle'
    case AppState.ERROR:
      return 'mdi-alert-circle'
    default:
      return 'mdi-help-circle'
  }
})

const statusText = computed(() => {
  switch (store.appState) {
    case AppState.IDLE:
      return 'No data loaded'
    case AppState.READY:
      return 'Ready to assign teams'
    case AppState.RUNNING:
      return 'Assigning teams...'
    case AppState.COMPLETE:
      return 'Teams assigned'
    case AppState.ERROR:
      return 'Error occurred'
    default:
      return 'Unknown'
  }
})
</script>

<style scoped>
.info-item {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
}
</style>
