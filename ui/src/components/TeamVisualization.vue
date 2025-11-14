<template>
  <v-card v-if="store.results">
    <v-card-title>Team Composition Analysis</v-card-title>

    <v-card-text>
      <v-row>
        <!-- Team size distribution bar chart -->
        <v-col cols="12" md="6">
          <div class="chart-container">
            <h3 class="text-subtitle-2 mb-4">Team Size Distribution</h3>
            <Bar :data="teamSizeChartData" :options="barChartOptions" />
          </div>
        </v-col>

        <!-- Constraint satisfaction (if any numeric constraints) -->
        <v-col cols="12" md="6">
          <div class="chart-container">
            <h3 class="text-subtitle-2 mb-4">Participants per Team</h3>
            <Bar :data="participantsPerTeamData" :options="horizontalBarOptions" />
          </div>
        </v-col>
      </v-row>

      <!-- Attribute distribution (for constrained attributes) -->
      <v-row v-if="store.constraints.length > 0">
        <v-col
          v-for="constraint in displayableConstraints"
          :key="constraint.attribute"
          cols="12"
          md="6"
        >
          <div class="chart-container">
            <h3 class="text-subtitle-2 mb-4">
              {{ formatAttributeName(constraint.attribute) }} Distribution
              <v-chip size="x-small" class="ml-2">{{ constraint.type }}</v-chip>
            </h3>
            <Pie
              v-if="getAttributeDistribution(constraint.attribute)"
              :data="getAttributeDistribution(constraint.attribute)!"
              :options="pieChartOptions"
            />
            <v-alert v-else type="info" variant="tonal" density="compact">
              No data available for this attribute
            </v-alert>
          </div>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Bar, Pie } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement
} from 'chart.js'
import { useTeamFormationStore } from '@/stores/teamFormation'

// Register Chart.js components
ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement)

const store = useTeamFormationStore()

// Chart options
const barChartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        stepSize: 1
      }
    }
  }
}

const horizontalBarOptions = {
  ...barChartOptions,
  indexAxis: 'y' as const,
  scales: {
    x: {
      beginAtZero: true,
      ticks: {
        stepSize: 1
      }
    }
  }
}

const pieChartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      position: 'right' as const
    }
  }
}

// Team size distribution chart
const teamSizeChartData = computed(() => {
  const sizes = store.teamSummaries.map(t => t.member_count)
  const uniqueSizes = [...new Set(sizes)].sort((a, b) => a - b)

  const counts = uniqueSizes.map(size => sizes.filter(s => s === size).length)

  return {
    labels: uniqueSizes.map(s => `Size ${s}`),
    datasets: [
      {
        label: 'Number of Teams',
        data: counts,
        backgroundColor: uniqueSizes.map(size => {
          const target = store.targetTeamSize
          if (size === target) return 'rgba(76, 175, 80, 0.7)' // Green
          if (Math.abs(size - target) === 1) return 'rgba(255, 193, 7, 0.7)' // Yellow
          return 'rgba(244, 67, 54, 0.7)' // Red
        })
      }
    ]
  }
})

// Participants per team chart
const participantsPerTeamData = computed(() => {
  return {
    labels: store.teamSummaries.map(t => `Team ${t.team_number}`),
    datasets: [
      {
        label: 'Members',
        data: store.teamSummaries.map(t => t.member_count),
        backgroundColor: 'rgba(25, 118, 210, 0.7)'
      }
    ]
  }
})

// Get displayable constraints (non-numeric for now)
const displayableConstraints = computed(() => {
  return store.constraints.filter(c => c.type !== 'cluster_numeric').slice(0, 4)
})

function formatAttributeName(attr: string): string {
  return attr
    .replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function getAttributeDistribution(attribute: string) {
  if (!store.results) return null

  // Count occurrences of each value
  const valueCounts = new Map<string, number>()

  store.results.forEach(participant => {
    const value = participant[attribute]
    if (value !== undefined && value !== null) {
      const strValue = String(value)
      valueCounts.set(strValue, (valueCounts.get(strValue) || 0) + 1)
    }
  })

  if (valueCounts.size === 0) return null

  // Limit to top 8 values for readability
  const sortedEntries = Array.from(valueCounts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)

  const colors = [
    'rgba(255, 99, 132, 0.7)',
    'rgba(54, 162, 235, 0.7)',
    'rgba(255, 206, 86, 0.7)',
    'rgba(75, 192, 192, 0.7)',
    'rgba(153, 102, 255, 0.7)',
    'rgba(255, 159, 64, 0.7)',
    'rgba(199, 199, 199, 0.7)',
    'rgba(83, 102, 255, 0.7)'
  ]

  return {
    labels: sortedEntries.map(e => e[0]),
    datasets: [
      {
        data: sortedEntries.map(e => e[1]),
        backgroundColor: colors.slice(0, sortedEntries.length)
      }
    ]
  }
}
</script>

<style scoped>
.chart-container {
  padding: 16px;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  min-height: 300px;
}
</style>
