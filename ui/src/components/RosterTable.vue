<template>
  <v-card>
    <v-card-title class="d-flex justify-space-between align-center">
      <span>Participant Roster</span>
      <div v-if="store.hasParticipants">
        <v-btn
          color="success"
          size="small"
          prepend-icon="mdi-download"
          class="mr-2"
          @click="handleExportCSV"
        >
          Export CSV
        </v-btn>
        <v-btn
          color="success"
          size="small"
          prepend-icon="mdi-code-json"
          @click="handleExportJSON"
        >
          Export JSON
        </v-btn>
      </div>
    </v-card-title>

    <v-card-text v-if="!store.hasParticipants">
      <v-alert type="info" variant="tonal">
        No participant data loaded. Please upload a CSV file to get started.
      </v-alert>
    </v-card-text>

    <v-card-text v-else>
      <!-- Search filter -->
      <v-text-field
        v-model="search"
        prepend-inner-icon="mdi-magnify"
        label="Search participants"
        single-line
        hide-details
        clearable
        class="mb-4"
      ></v-text-field>

      <!-- Data table -->
      <v-data-table
        :headers="headers"
        :items="store.participants"
        :search="search"
        :items-per-page="itemsPerPage"
        :items-per-page-options="[10, 25, 50, 100, -1]"
        class="elevation-1"
        density="comfortable"
      >
        <!-- Highlight team_number column if present -->
        <template v-slot:item.team_number="{ value }">
          <v-chip
            v-if="value !== undefined && value !== null"
            color="primary"
            size="small"
          >
            Team {{ value }}
          </v-chip>
          <span v-else class="text-grey">—</span>
        </template>

        <!-- Footer with stats -->
        <template v-slot:bottom>
          <div class="text-center pa-2">
            <span class="text-caption">
              Total: {{ store.participants.length }} participants
            </span>
          </div>
        </template>
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useTeamFormationStore } from '@/stores/teamFormation'
import { exportToCSV, exportToJSON } from '@/services/csvParser'

const store = useTeamFormationStore()

const search = ref('')
const itemsPerPage = ref(25)

// Generate headers dynamically from participant data
const headers = computed(() => {
  if (store.participants.length === 0) return []

  const firstParticipant = store.participants[0]
  const keys = Object.keys(firstParticipant)

  return keys.map(key => ({
    title: formatColumnName(key),
    key: key,
    value: key,
    sortable: true
  }))
})

function formatColumnName(key: string): string {
  // Convert snake_case or camelCase to Title Case
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
    .trim()
}

function handleExportCSV() {
  const data = store.results || store.participants
  const filename = store.results
    ? `team-assignments-${Date.now()}.csv`
    : `participants-${Date.now()}.csv`
  exportToCSV(data, filename)
}

function handleExportJSON() {
  const data = store.results || store.participants
  const filename = store.results
    ? `team-assignments-${Date.now()}.json`
    : `participants-${Date.now()}.json`
  exportToJSON(data, filename)
}
</script>

<style scoped>
/* Add any custom styling here */
</style>
