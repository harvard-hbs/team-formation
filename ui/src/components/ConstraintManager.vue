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

      <!-- Constraints table -->
      <v-table v-if="store.constraints.length > 0" density="compact" class="constraints-table">
        <thead>
          <tr>
            <th class="text-left">Attribute</th>
            <th class="text-left">
              <span>Rule Type</span>
              <v-tooltip location="bottom" max-width="400">
                <template v-slot:activator="{ props }">
                  <v-icon v-bind="props" size="small" class="ml-1">mdi-information-outline</v-icon>
                </template>
                <div>
                  <div class="mb-2"><strong>Cluster:</strong> Group participants with shared discrete attribute values together in teams</div>
                  <div class="mb-2"><strong>Cluster Numeric:</strong> Minimize numeric attribute ranges within teams (e.g., similar experience levels)</div>
                  <div class="mb-2"><strong>Different:</strong> Ensure teams don't share specific attribute values (e.g., no two people from same department)</div>
                  <div><strong>Diversify:</strong> Match team attribute distributions to overall population (e.g., gender balance)</div>
                </div>
              </v-tooltip>
            </th>
            <th class="text-left weight-column">Weight</th>
            <th class="text-center actions-column"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(constraint, index) in store.constraints"
            :key="index"
            class="constraint-row"
          >
            <!-- Attribute selector -->
            <td>
              <v-select
                :model-value="constraint.attribute"
                :items="store.availableAttributes"
                density="compact"
                variant="underlined"
                hide-details="auto"
                :error="!isAttributeValid(constraint.attribute)"
                :error-messages="getAttributeError(constraint.attribute)"
                @update:model-value="(value) => updateConstraint(index, 'attribute', value)"
              ></v-select>
            </td>

            <!-- Type selector -->
            <td>
              <v-select
                :model-value="constraint.type"
                :items="constraintTypes"
                density="compact"
                variant="underlined"
                hide-details
                @update:model-value="(value) => updateConstraint(index, 'type', value)"
              ></v-select>
            </td>

            <!-- Weight input -->
            <td>
              <v-text-field
                :model-value="constraint.weight"
                type="number"
                density="compact"
                variant="underlined"
                hide-details="auto"
                :error="constraint.weight <= 0"
                :error-messages="constraint.weight <= 0 ? 'Must be > 0' : ''"
                @update:model-value="(value) => updateConstraint(index, 'weight', parseFloat(value || '0'))"
              ></v-text-field>
            </td>

            <!-- Delete button -->
            <td class="text-center">
              <v-btn
                icon="mdi-delete"
                size="x-small"
                color="error"
                variant="text"
                @click="removeConstraint(index)"
              ></v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>

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
.constraints-table {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.constraints-table :deep(thead) {
  background-color: #fafafa;
}

.constraints-table :deep(th) {
  font-weight: 600;
  padding: 8px 12px !important;
  white-space: nowrap;
}

.constraints-table :deep(td) {
  padding: 4px 12px !important;
  vertical-align: middle;
}

.weight-column {
  width: 120px;
}

.actions-column {
  width: 60px;
}

.constraint-row:hover {
  background-color: #f5f5f5;
}

/* Make form fields more compact within table cells */
.constraints-table :deep(.v-field) {
  font-size: 0.875rem;
}

.constraints-table :deep(.v-field__input) {
  min-height: 32px;
  padding-top: 4px;
  padding-bottom: 4px;
}
</style>
