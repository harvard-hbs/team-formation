<template>
  <v-card>
    <v-card-title>Upload Participant Roster</v-card-title>
    <v-card-text>
      <v-file-input
        v-model="selectedFile"
        accept=".csv"
        label="Select CSV file"
        prepend-icon="mdi-file-delimited"
        show-size
        clearable
        @update:model-value="handleFileSelect"
        @click:clear="handleClear"
      ></v-file-input>

      <!-- Drag and drop area -->
      <div
        class="drop-zone"
        :class="{ 'drop-zone--active': isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
      >
        <v-icon size="48" color="grey">mdi-cloud-upload</v-icon>
        <p class="text-body-1 mt-2">Drag and drop CSV file here</p>
        <p class="text-caption text-grey">or use the file selector above</p>
      </div>

      <!-- Loading state -->
      <v-progress-linear
        v-if="loading"
        indeterminate
        color="primary"
        class="mt-4"
      ></v-progress-linear>

      <!-- Success message -->
      <v-alert
        v-if="parseResult && parseResult.success"
        type="success"
        class="mt-4"
        closable
        @click:close="parseResult = null"
      >
        Successfully loaded {{ parseResult.rowCount }} participants with {{ parseResult.columnCount }} attributes
      </v-alert>

      <!-- Error message -->
      <v-alert
        v-if="parseResult && !parseResult.success"
        type="error"
        class="mt-4"
        closable
        @click:close="parseResult = null"
      >
        {{ parseResult.error }}
      </v-alert>

      <!-- Validation warnings -->
      <v-alert
        v-if="validationResult && validationResult.warnings.length > 0"
        type="warning"
        class="mt-4"
      >
        <div v-for="(warning, index) in validationResult.warnings" :key="index">
          {{ warning }}
        </div>
      </v-alert>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useTeamFormationStore } from '@/stores/teamFormation'
import { parseCSV, validateParticipantData } from '@/services/csvParser'
import type { ParseResult } from '@/services/csvParser'

const store = useTeamFormationStore()

const selectedFile = ref<File[] | null>(null)
const loading = ref(false)
const isDragging = ref(false)
const parseResult = ref<ParseResult | null>(null)
const validationResult = ref<any>(null)

async function handleFileSelect(files: File | File[] | null) {
  if (!files) return

  const file = Array.isArray(files) ? files[0] : files
  await processFile(file)
}

async function handleDrop(event: DragEvent) {
  isDragging.value = false

  const files = event.dataTransfer?.files
  if (!files || files.length === 0) return

  const file = files[0]

  // Check if it's a CSV file
  if (!file.name.endsWith('.csv')) {
    parseResult.value = {
      success: false,
      error: 'Please upload a CSV file'
    }
    return
  }

  selectedFile.value = [file]
  await processFile(file)
}

async function processFile(file: File) {
  loading.value = true
  parseResult.value = null
  validationResult.value = null

  try {
    const result = await parseCSV(file)
    parseResult.value = result

    if (result.success && result.data) {
      // Validate the data
      validationResult.value = validateParticipantData(result.data)

      if (validationResult.value.valid || validationResult.value.warnings.length > 0) {
        // Load into store
        store.loadParticipants(result.data)
      }
    }
  } catch (error) {
    parseResult.value = {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    }
  } finally {
    loading.value = false
  }
}

function handleClear() {
  selectedFile.value = null
  parseResult.value = null
  validationResult.value = null
}
</script>

<style scoped>
.drop-zone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
  margin-top: 16px;
}

.drop-zone--active {
  border-color: #1976D2;
  background-color: rgba(25, 118, 210, 0.05);
}

.drop-zone:hover {
  border-color: #1976D2;
  background-color: rgba(25, 118, 210, 0.02);
}
</style>
