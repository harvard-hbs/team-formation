<template>
  <v-app>
    <v-app-bar color="primary" elevation="0" height="64">
      <v-app-bar-title class="text-body-1 font-weight-regular">
        <v-icon class="mr-2" size="small">mdi-account-group</v-icon>
        Team Formation Service
      </v-app-bar-title>
    </v-app-bar>

    <v-main class="bg-grey-lighten-4">
      <v-container fluid class="pa-6">
        <v-row>
          <v-col cols="12">
            <TeamInformation />
          </v-col>
        </v-row>

        <v-row class="mt-6">
          <v-col cols="12">
            <RosterSection />
          </v-col>
        </v-row>

        <v-row class="mt-6">
          <v-col cols="12">
            <TeamsSection />
          </v-col>
        </v-row>
      </v-container>
    </v-main>

    <v-footer app class="text-center">
      <v-col>
        <span class="text-caption">
          Powered by Google OR-Tools CP-SAT Solver | Built with Vue 3 + Vuetify
        </span>
      </v-col>
    </v-footer>
  </v-app>
</template>

<script setup lang="ts">
import TeamInformation from './components/TeamInformation.vue'
import RosterSection from './components/RosterSection.vue'
import TeamsSection from './components/TeamsSection.vue'
</script>

<style>
/* Global styles */
html {
  overflow-y: auto !important;
}

.v-container {
  max-width: 1600px;
}
</style>
