<template>
  <div class="roster-section">
    <h2 class="text-h4 font-weight-bold mb-4">Roster</h2>

    <v-row>
      <v-col cols="12">
        <RosterTable />
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import RosterTable from './RosterTable.vue'
</script>

<style scoped>
.roster-section {
  margin-bottom: 32px;
}
</style>
