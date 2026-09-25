import type { Participant } from '@/types'

/**
 * Column contract for the HBS Online Learner Dashboard roster upload.
 *
 * The Dashboard accepts exactly these columns, in this order, under these
 * header names. Changing the Dashboard's expected schema is a one-line edit
 * here; nothing else in this module hard-codes a column name.
 */
export const DASHBOARD_COLUMNS: ReadonlyArray<{ source: string; header: string }> = [
  { source: 'first_name', header: 'First Name' },
  { source: 'last_name', header: 'Last Name' },
  { source: 'email_id', header: 'Business Email Address' },
  { source: 'hbx_id', header: 'HBS Online ID' },
  { source: 'wave_code', header: 'Bodhi Wave Code' },
  { source: 'profile_image_url', header: 'Profile Photo URL' },
  { source: 'team_number', header: 'Team Name' }
]

/** Source column that carries the solver's zero-indexed team assignment. */
const TEAM_COLUMN = 'team_number'

export type DashboardRow = Record<string, string | number | boolean>

/**
 * Find the key a participant actually uses for a contract column.
 *
 * Rosters reach us with varying header casing -- FIRST_NAME from one export,
 * first_name from another -- so source columns are matched case-insensitively.
 * An exact match always wins; otherwise the first key that matches ignoring
 * case, in key order, is used. Returns undefined when the row has no such key.
 */
function resolveKey(participant: Participant, source: string): string | undefined {
  if (source in participant) return source

  const wanted = source.toLowerCase()

  return Object.keys(participant).find(key => key.toLowerCase() === wanted)
}

/**
 * Report which required source columns are absent from the assignment results.
 *
 * Matching ignores header case, so a roster carrying FIRST_NAME satisfies the
 * first_name requirement. A column counts as present when any participant
 * record carries it, so a column that exists but is blank for some
 * participants is not reported as missing. Missing columns are reported under
 * their canonical contract names, whatever casing the roster uses. Returns an
 * empty array when the results satisfy the contract.
 */
export function findMissingColumns(participants: Participant[]): string[] {
  const present = new Set<string>()

  participants.forEach(participant => {
    Object.keys(participant).forEach(key => present.add(key.toLowerCase()))
  })

  return DASHBOARD_COLUMNS
    .map(column => column.source)
    .filter(source => !present.has(source.toLowerCase()))
}

/**
 * Reshape assignment results into Dashboard rows.
 *
 * Selects only the contract columns, matching their roster headers
 * case-insensitively, renames them to their Dashboard headers, and renders the
 * zero-indexed team number as the label "Team N" (team 0 becomes "Team 1").
 * Every other value passes through unchanged; a null, undefined, or empty
 * value becomes an empty cell. Rows are ordered by team number ascending,
 * preserving the input order within a team, and participants with no team
 * assignment are omitted.
 */
export function buildDashboardRows(participants: Participant[]): DashboardRow[] {
  const teamNumberOf = (participant: Participant): number => {
    const key = resolveKey(participant, TEAM_COLUMN)

    return key === undefined ? NaN : Number(participant[key])
  }

  const assigned = participants.filter(participant =>
    Number.isFinite(teamNumberOf(participant))
  )

  // Array.prototype.sort is stable, so members keep their input order
  // within a team.
  const ordered = [...assigned].sort(
    (a, b) => teamNumberOf(a) - teamNumberOf(b)
  )

  return ordered.map(participant => {
    const row: DashboardRow = {}

    DASHBOARD_COLUMNS.forEach(({ source, header }) => {
      if (source === TEAM_COLUMN) {
        row[header] = `Team ${teamNumberOf(participant) + 1}`
        return
      }

      const key = resolveKey(participant, source)
      const value = key === undefined ? undefined : participant[key]
      row[header] = value === null || value === undefined ? '' : value
    })

    return row
  })
}

/**
 * Build and download the Dashboard roster as a single-sheet .xlsx workbook.
 *
 * Callers are expected to run findMissingColumns first: this function assumes
 * the column contract is satisfied and does not validate. The header row is
 * written from DASHBOARD_COLUMNS so sheet column order never depends on
 * object key order.
 *
 * ExcelJS is imported dynamically so its ~950 kB of workbook machinery stays
 * out of the initial bundle and is fetched only when someone exports.
 */
export async function exportToDashboardXlsx(
  participants: Participant[],
  filename: string = 'dashboard-roster.xlsx'
): Promise<void> {
  const { default: ExcelJS } = await import('exceljs')

  const workbook = new ExcelJS.Workbook()
  const sheet = workbook.addWorksheet('Roster')

  const headers = DASHBOARD_COLUMNS.map(column => column.header)
  sheet.addRow(headers)

  buildDashboardRows(participants).forEach(row => {
    sheet.addRow(headers.map(header => row[header]))
  })

  const buffer = await workbook.xlsx.writeBuffer()

  const blob = new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  })
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
