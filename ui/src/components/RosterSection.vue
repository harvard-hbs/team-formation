<template>
  <div class="roster-section">
    <h2 class="text-h5 mb-4">
      <v-icon class="mr-2">mdi-account-multiple</v-icon>
      Roster
    </h2>

    <v-row>
      <v-col cols="12">
        <FileUpload />
      </v-col>
    </v-row>

    <v-row v-if="store.hasParticipants">
      <v-col cols="12">
        <RosterTable />
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { useTeamFormationStore } from '@/stores/teamFormation'
import FileUpload from './FileUpload.vue'
import RosterTable from './RosterTable.vue'

const store = useTeamFormationStore()
</script>

<style scoped>
.roster-section {
  margin-bottom: 32px;
}
</style>
