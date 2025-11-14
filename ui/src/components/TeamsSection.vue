<template>
  <div class="teams-section">
    <h2 class="text-h4 font-weight-bold mb-4">Teams</h2>

    <v-card elevation="0" class="teams-container pa-6">
      <v-row>
        <!-- Left column: Constraints and Settings -->
        <v-col cols="12" md="6">
          <v-row>
            <v-col cols="12">
              <ConstraintManager />
            </v-col>

            <v-col cols="12">
              <TeamSettings />
            </v-col>
          </v-row>
        </v-col>

        <!-- Right column: Progress -->
        <v-col cols="12" md="6">
          <ProgressStream />
        </v-col>
      </v-row>
    </v-card>

    <!-- Results section (full width) -->
    <v-row v-if="store.results" class="mt-4">
      <v-col cols="12">
        <ResultsTable />
      </v-col>

      <v-col cols="12">
        <TeamVisualization />
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { useTeamFormationStore } from '@/stores/teamFormation'
import ConstraintManager from './ConstraintManager.vue'
import TeamSettings from './TeamSettings.vue'
import ProgressStream from './ProgressStream.vue'
import ResultsTable from './ResultsTable.vue'
import TeamVisualization from './TeamVisualization.vue'

const store = useTeamFormationStore()
</script>

<style scoped>
.teams-section {
  margin-bottom: 32px;
}

.teams-container {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}
</style>
