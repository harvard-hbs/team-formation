<template>
  <div class="teams-section">
    <h2 class="text-h5 mb-4">
      <v-icon class="mr-2">mdi-account-group</v-icon>
      Teams
    </h2>

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

    <!-- Results section (full width) -->
    <v-row v-if="store.results">
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
</style>
