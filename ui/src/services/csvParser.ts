import Papa from 'papaparse'
import type { Participant } from '@/types'

export interface ParseResult {
  success: boolean
  data?: Participant[]
  error?: string
  rowCount?: number
  columnCount?: number
}

/**
 * Parse CSV file to JSON array of participants
 */
export function parseCSV(file: File): Promise<ParseResult> {
  return new Promise((resolve) => {
    Papa.parse(file, {
      header: true, // First row as column headers
      skipEmptyLines: true,
      dynamicTyping: true, // Automatically convert numbers
      transform: (value: string) => {
        // Trim whitespace
        return value.trim()
      },
      complete: (results) => {
        if (results.errors.length > 0) {
          const errorMessages = results.errors
            .map(err => `Row ${err.row}: ${err.message}`)
            .join('; ')

          resolve({
            success: false,
            error: `CSV parsing errors: ${errorMessages}`
          })
          return
        }

        if (!results.data || results.data.length === 0) {
          resolve({
            success: false,
            error: 'CSV file is empty or has no valid data'
          })
          return
        }

        // Get column count from first row
        const firstRow = results.data[0] as any
        const columnCount = Object.keys(firstRow).length

        if (columnCount === 0) {
          resolve({
            success: false,
            error: 'CSV file has no columns'
          })
          return
        }

        resolve({
          success: true,
          data: results.data as Participant[],
          rowCount: results.data.length,
          columnCount
        })
      },
      error: (error) => {
        resolve({
          success: false,
          error: `Failed to parse CSV: ${error.message}`
        })
      }
    })
  })
}

/**
 * Export participants to CSV format
 */
export function exportToCSV(data: Participant[], filename: string = 'team-assignments.csv'): void {
  const csv = Papa.unparse(data, {
    quotes: true, // Quote all fields
    header: true
  })

  // Create blob and download
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)

  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}

/**
 * Export participants to JSON format
 */
export function exportToJSON(data: Participant[], filename: string = 'team-assignments.json'): void {
  const json = JSON.stringify(data, null, 2)

  const blob = new Blob([json], { type: 'application/json;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)

  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}

/**
 * Validate CSV data structure
 */
export function validateParticipantData(data: Participant[]): {
  valid: boolean
  errors: string[]
  warnings: string[]
} {
  const errors: string[] = []
  const warnings: string[] = []

  // Check if data is empty
  if (data.length === 0) {
    errors.push('No participant data provided')
    return { valid: false, errors, warnings }
  }

  // Check for unique ID field (common identifiers)
  const idFields = ['id', 'ID', 'student_id', 'email', 'participant_id']
  const firstRow = data[0]
  const hasIdField = idFields.some(field => field in firstRow)

  if (!hasIdField) {
    warnings.push('No standard ID field found. Consider adding an "id" column for identification.')
  }

  // Check for very small dataset
  if (data.length < 3) {
    warnings.push(`Only ${data.length} participants. Team formation requires at least 3 participants.`)
  }

  // Check for consistent schema
  const firstRowKeys = Object.keys(firstRow)
  let inconsistentRows = 0

  data.forEach((row) => {
    const rowKeys = Object.keys(row)
    if (rowKeys.length !== firstRowKeys.length) {
      inconsistentRows++
    }
  })

  if (inconsistentRows > 0) {
    warnings.push(`${inconsistentRows} rows have different column counts. This may indicate data quality issues.`)
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  }
}
