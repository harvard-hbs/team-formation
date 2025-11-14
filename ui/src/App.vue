<template>
  <v-app>
    <v-app-bar color="primary" prominent elevation="2">
      <v-app-bar-title>
        <v-icon class="mr-2" size="large">mdi-account-group</v-icon>
        Team Formation Service
      </v-app-bar-title>
    </v-app-bar>

    <v-main>
      <v-container fluid class="pa-6">
        <v-row>
          <v-col cols="12">
            <TeamInformation />
          </v-col>
        </v-row>

        <v-divider class="my-6"></v-divider>

        <v-row>
          <v-col cols="12">
            <RosterSection />
          </v-col>
        </v-row>

        <v-divider class="my-6"></v-divider>

        <v-row>
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
