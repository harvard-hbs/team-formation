<template>
  <span>
    <!-- Preset selector dropdown -->
    <v-menu>
      <template v-slot:activator="{ props }">
        <v-btn
          color="secondary"
          size="small"
          prepend-icon="mdi-bookmark"
          v-bind="props"
        >
          Presets
        </v-btn>
      </template>

      <v-card min-width="300">
        <v-card-title>Constraint Presets</v-card-title>
        <v-divider></v-divider>

        <v-list v-if="store.presets.length > 0">
          <v-list-item
            v-for="(preset, index) in store.presets"
            :key="index"
          >
            <v-list-item-title>{{ preset.name }}</v-list-item-title>
            <v-list-item-subtitle v-if="preset.description">
              {{ preset.description }}
            </v-list-item-subtitle>
            <v-list-item-subtitle class="text-caption">
              {{ preset.constraints.length }} constraints, Target size: {{ preset.target_team_size }}
            </v-list-item-subtitle>

            <template v-slot:append>
              <v-btn
                icon="mdi-download"
                size="x-small"
                variant="text"
                @click="loadPreset(index)"
              ></v-btn>
              <v-btn
                icon="mdi-delete"
                size="x-small"
                variant="text"
                color="error"
                @click="deletePreset(index)"
              ></v-btn>
            </template>
          </v-list-item>
        </v-list>

        <v-card-text v-else>
          <v-alert type="info" variant="tonal">
            No saved presets yet.
          </v-alert>
        </v-card-text>

        <v-divider></v-divider>
        <v-card-actions>
          <v-btn
            color="primary"
            variant="tonal"
            size="small"
            prepend-icon="mdi-content-save"
            :disabled="!canSave"
            @click="openSaveDialog"
          >
            Save Current
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-menu>

    <!-- Save preset dialog -->
    <v-dialog v-model="saveDialog" max-width="500">
      <v-card>
        <v-card-title>Save Constraint Preset</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="presetName"
            label="Preset Name"
            placeholder="e.g., MBA Team Formation"
            required
            autofocus
          ></v-text-field>

          <v-textarea
            v-model="presetDescription"
            label="Description (optional)"
            placeholder="Describe this preset configuration..."
            rows="2"
          ></v-textarea>

          <div class="text-caption text-grey mt-2">
            This will save {{ store.constraints.length }} constraints and current team settings.
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="saveDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            :disabled="!presetName.trim()"
            @click="savePreset"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar for feedback -->
    <v-snackbar v-model="snackbar" :timeout="3000" :color="snackbarColor">
      {{ snackbarMessage }}
    </v-snackbar>
  </span>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useTeamFormationStore } from '@/stores/teamFormation'

const store = useTeamFormationStore()

const saveDialog = ref(false)
const presetName = ref('')
const presetDescription = ref('')
const snackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

const canSave = computed(() => {
  return store.constraints.length > 0
})

function openSaveDialog() {
  presetName.value = ''
  presetDescription.value = ''
  saveDialog.value = true
}

function savePreset() {
  if (!presetName.value.trim()) return

  try {
    store.savePreset(presetName.value.trim(), presetDescription.value.trim() || undefined)
    saveDialog.value = false
    showSnackbar('Preset saved successfully!', 'success')
  } catch (error) {
    showSnackbar('Failed to save preset', 'error')
  }
}

function loadPreset(index: number) {
  try {
    store.loadPreset(index)
    showSnackbar('Preset loaded successfully!', 'success')
  } catch (error) {
    showSnackbar('Failed to load preset', 'error')
  }
}

function deletePreset(index: number) {
  if (confirm('Are you sure you want to delete this preset?')) {
    try {
      store.deletePreset(index)
      showSnackbar('Preset deleted', 'info')
    } catch (error) {
      showSnackbar('Failed to delete preset', 'error')
    }
  }
}

function showSnackbar(message: string, color: string) {
  snackbarMessage.value = message
  snackbarColor.value = color
  snackbar.value = true
}
</script>
