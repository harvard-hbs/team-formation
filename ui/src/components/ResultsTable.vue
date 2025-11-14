<template>
  <v-card v-if="store.results">
    <v-card-title>Team Assignments</v-card-title>

    <v-card-text>
      <!-- Teams grouped display -->
      <v-expansion-panels variant="accordion">
        <v-expansion-panel
          v-for="team in store.teamSummaries"
          :key="team.team_number"
        >
          <v-expansion-panel-title>
            <div class="d-flex align-center justify-space-between w-100">
              <div class="d-flex align-center">
                <v-chip color="primary" size="small" class="mr-2">
                  Team {{ team.team_number }}
                </v-chip>
                <span class="text-body-2">
                  {{ team.member_count }} member{{ team.member_count !== 1 ? 's' : '' }}
                </span>
              </div>

              <!-- Size indicator -->
              <v-chip
                :color="getSizeColor(team.member_count)"
                size="x-small"
                variant="tonal"
                class="mr-4"
              >
                {{ getSizeLabel(team.member_count) }}
              </v-chip>
            </div>
          </v-expansion-panel-title>

          <v-expansion-panel-text>
            <v-table density="compact">
              <thead>
                <tr>
                  <th v-for="col in displayColumns" :key="col">
                    {{ formatColumnName(col) }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(member, index) in team.members" :key="index">
                  <td v-for="col in displayColumns" :key="col">
                    <span v-if="Array.isArray(member[col])">
                      {{ member[col].join(', ') }}
                    </span>
                    <span v-else>
                      {{ member[col] ?? '—' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>

      <!-- Team size distribution chart -->
      <div class="mt-6">
        <v-row>
          <v-col cols="12" md="6">
            <div class="text-subtitle-2 mb-2">Team Size Distribution</div>
            <v-chip
              v-for="size in uniqueSizes"
              :key="size"
              :color="getSizeColor(size)"
              size="small"
              class="mr-2 mb-2"
            >
              Size {{ size }}: {{ getCountForSize(size) }} team{{ getCountForSize(size) !== 1 ? 's' : '' }}
            </v-chip>
          </v-col>

          <v-col cols="12" md="6">
            <div class="text-subtitle-2 mb-2">Summary Statistics</div>
            <div class="text-body-2">
              <div>Average team size: {{ averageTeamSize.toFixed(1) }}</div>
              <div>Min size: {{ minTeamSize }}</div>
              <div>Max size: {{ maxTeamSize }}</div>
            </div>
          </v-col>
        </v-row>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTeamFormationStore } from '@/stores/teamFormation'

const store = useTeamFormationStore()

// Get columns to display (excluding team_number as it's in the header)
const displayColumns = computed(() => {
  if (!store.results || store.results.length === 0) return []

  const firstMember = store.results[0]
  return Object.keys(firstMember).filter(key => key !== 'team_number')
})

function formatColumnName(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
    .trim()
}

// Team size analysis
const teamSizes = computed(() => {
  return store.teamSummaries.map(t => t.member_count)
})

const uniqueSizes = computed(() => {
  return [...new Set(teamSizes.value)].sort((a, b) => a - b)
})

const averageTeamSize = computed(() => {
  if (teamSizes.value.length === 0) return 0
  return teamSizes.value.reduce((a, b) => a + b, 0) / teamSizes.value.length
})

const minTeamSize = computed(() => {
  return teamSizes.value.length > 0 ? Math.min(...teamSizes.value) : 0
})

const maxTeamSize = computed(() => {
  return teamSizes.value.length > 0 ? Math.max(...teamSizes.value) : 0
})

function getCountForSize(size: number): number {
  return teamSizes.value.filter(s => s === size).length
}

function getSizeColor(size: number): string {
  const target = store.targetTeamSize
  if (size === target) return 'success'
  if (Math.abs(size - target) === 1) return 'warning'
  return 'error'
}

function getSizeLabel(size: number): string {
  const target = store.targetTeamSize
  if (size === target) return 'Target'
  if (size < target) return 'Under'
  return 'Over'
}
</script>

<style scoped>
.w-100 {
  width: 100%;
}
</style>
