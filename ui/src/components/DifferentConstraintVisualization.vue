<template>
  <div v-if="store.differentConstraintEvaluations.length > 0">
    <v-row>
      <v-col
        v-for="evaluation in store.differentConstraintEvaluations"
        :key="evaluation.attribute"
        cols="12"
        md="6"
      >
        <div class="chart-container">
          <h3 class="text-subtitle-2 mb-2">
            {{ formatAttributeName(evaluation.attribute) }} Sameness
            <v-chip size="x-small" class="ml-2">different</v-chip>
          </h3>
          <div class="text-caption text-medium-emphasis mb-3">
            Shared values per team (0 = perfect diversity)
          </div>

          <!-- Summary stats -->
          <div class="d-flex ga-3 mb-3">
            <v-chip
              size="small"
              :color="summaryStats(evaluation).perfectCount === evaluation.teams.length ? 'success' : 'default'"
              variant="tonal"
            >
              {{ summaryStats(evaluation).perfectCount }}/{{ evaluation.teams.length }} perfect teams
            </v-chip>
            <v-chip size="small" variant="tonal">
              Avg: {{ summaryStats(evaluation).avgMissed.toFixed(1) }} shared
            </v-chip>
          </div>

          <!-- Bar chart -->
          <Bar :data="getChartData(evaluation)" :options="barChartOptions" />
        </div>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { Bar } from "vue-chartjs"
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from "chart.js"
import { useTeamFormationStore } from "@/stores/teamFormation"
import type { DifferentConstraintEvaluation } from "@/types"

// Register Chart.js components
ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

const store = useTeamFormationStore()

// Chart options
const barChartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      callbacks: {
        label: function(context: any) {
          const value = context.parsed.y
          if (value === 0) return "Perfect - all unique values"
          return `${value} participant${value > 1 ? "s" : ""} sharing a value`
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: "Shared Values"
      },
      ticks: {
        stepSize: 1
      }
    },
    x: {
      title: {
        display: true,
        text: "Team"
      }
    }
  }
}

function formatAttributeName(attr: string): string {
  return attr
    .replace(/_/g, " ")
    .split(" ")
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ")
}

function getBarColor(missed: number): string {
  if (missed === 0) return "rgba(76, 175, 80, 0.7)"   // Green - perfect
  if (missed <= 2) return "rgba(255, 193, 7, 0.7)"   // Yellow - 1-2
  return "rgba(244, 67, 54, 0.7)"                     // Red - 3+
}

function getChartData(evaluation: DifferentConstraintEvaluation) {
  return {
    labels: evaluation.teams.map(t => `${t.team_number}`),
    datasets: [
      {
        label: "Shared Values",
        data: evaluation.teams.map(t => t.missed),
        backgroundColor: evaluation.teams.map(t => getBarColor(t.missed))
      }
    ]
  }
}

function summaryStats(evaluation: DifferentConstraintEvaluation) {
  const perfectCount = evaluation.teams.filter(t => t.missed === 0).length
  const totalMissed = evaluation.teams.reduce((sum, t) => sum + t.missed, 0)
  const avgMissed = evaluation.teams.length > 0 ? totalMissed / evaluation.teams.length : 0

  return {
    perfectCount,
    avgMissed
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
