<template>
  <v-card elevation="0">
    <v-card-title class="d-flex justify-space-between align-center px-0">
      <span class="text-h5 font-weight-bold">Constraints</span>
      <div>
        <PresetManager class="mr-2" />
        <v-btn
          color="accent"
          size="small"
          prepend-icon="mdi-plus"
          :disabled="!store.hasParticipants"
          @click="addNewConstraint"
        >
          Add Constraint
        </v-btn>
      </div>
    </v-card-title>

    <v-card-text class="px-0">
      <v-alert v-if="!store.hasParticipants" type="info" variant="tonal" class="mb-4">
        Upload participant data first to add constraints.
      </v-alert>

      <div v-else-if="store.constraints.length === 0">
        <v-alert type="info" variant="tonal">
          No constraints defined. Click "Add Constraint" to get started.
        </v-alert>
      </div>

      <!-- Constraints list -->
      <v-list v-if="store.constraints.length > 0" class="pa-0">
        <v-list-item
          v-for="(constraint, index) in store.constraints"
          :key="index"
          class="constraint-item mb-2 pa-3 border rounded"
        >
          <v-row dense align="center">
            <!-- Attribute selector -->
            <v-col cols="12" sm="4">
              <v-select
                :model-value="constraint.attribute"
                :items="store.availableAttributes"
                label="Attribute"
                density="compact"
                :error="!isAttributeValid(constraint.attribute)"
                :error-messages="getAttributeError(constraint.attribute)"
                @update:model-value="(value) => updateConstraint(index, 'attribute', value)"
              >
                <template v-slot:prepend>
                  <v-icon size="small">mdi-format-list-bulleted</v-icon>
                </template>
              </v-select>
            </v-col>

            <!-- Type selector -->
            <v-col cols="12" sm="3">
              <v-select
                :model-value="constraint.type"
                :items="constraintTypes"
                label="Rule Type"
                density="compact"
                @update:model-value="(value) => updateConstraint(index, 'type', value)"
              >
                <template v-slot:prepend>
                  <v-icon size="small">mdi-cog</v-icon>
                </template>
              </v-select>
            </v-col>

            <!-- Weight input -->
            <v-col cols="12" sm="3">
              <v-text-field
                :model-value="constraint.weight"
                label="Weight"
                type="number"
                density="compact"
                :error="constraint.weight <= 0"
                :error-messages="constraint.weight <= 0 ? 'Must be > 0' : ''"
                @update:model-value="(value) => updateConstraint(index, 'weight', parseFloat(value || '0'))"
              >
                <template v-slot:prepend>
                  <v-icon size="small">mdi-weight</v-icon>
                </template>
              </v-text-field>
            </v-col>

            <!-- Delete button -->
            <v-col cols="12" sm="2" class="text-right">
              <v-btn
                icon="mdi-delete"
                size="small"
                color="error"
                variant="text"
                @click="removeConstraint(index)"
              ></v-btn>
            </v-col>
          </v-row>

          <!-- Constraint type description -->
          <div class="text-caption text-grey mt-2">
            {{ getConstraintDescription(constraint.type) }}
          </div>
        </v-list-item>
      </v-list>

      <!-- Validation messages -->
      <v-alert
        v-if="validation && !validation.valid"
        type="error"
        class="mt-4"
      >
        <div v-for="(error, index) in validation.errors" :key="index">
          {{ error }}
        </div>
      </v-alert>

      <v-alert
        v-if="validation && validation.warnings.length > 0"
        type="warning"
        class="mt-4"
      >
        <div v-for="(warning, index) in validation.warnings" :key="index">
          {{ warning }}
        </div>
      </v-alert>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useTeamFormationStore } from '@/stores/teamFormation'
import type { ConstraintType } from '@/types'
import PresetManager from './PresetManager.vue'

const store = useTeamFormationStore()

const constraintTypes: { title: string; value: ConstraintType }[] = [
  { title: 'Cluster', value: 'cluster' },
  { title: 'Cluster Numeric', value: 'cluster_numeric' },
  { title: 'Different', value: 'different' },
  { title: 'Diversify', value: 'diversify' }
]

const validation = ref(store.validateConstraints())

// Watch for changes and revalidate
watch(
  () => [store.constraints, store.availableAttributes],
  () => {
    validation.value = store.validateConstraints()
  },
  { deep: true }
)

function addNewConstraint() {
  const defaultAttribute = store.availableAttributes[0] || ''
  store.addConstraint({
    attribute: defaultAttribute,
    type: 'cluster',
    weight: 1
  })
}

function updateConstraint(index: number, field: string, value: any) {
  const constraint = { ...store.constraints[index] }
  ;(constraint as any)[field] = value
  store.updateConstraint(index, constraint)
}

function removeConstraint(index: number) {
  store.removeConstraint(index)
}

function isAttributeValid(attribute: string): boolean {
  return store.availableAttributes.includes(attribute)
}

function getAttributeError(attribute: string): string {
  return isAttributeValid(attribute) ? '' : 'Attribute not found in data'
}

function getConstraintDescription(type: ConstraintType): string {
  switch (type) {
    case 'cluster':
      return 'Group participants with shared discrete attribute values together in teams'
    case 'cluster_numeric':
      return 'Minimize numeric attribute ranges within teams (e.g., similar experience levels)'
    case 'different':
      return 'Ensure teams don\'t share specific attribute values (e.g., no two people from same department)'
    case 'diversify':
      return 'Match team attribute distributions to overall population (e.g., gender balance)'
    default:
      return ''
  }
}
</script>

<style scoped>
.constraint-item {
  background-color: #fafafa;
}

.border {
  border: 1px solid #e0e0e0;
}
</style>
