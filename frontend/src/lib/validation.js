// Turns a validation workbook into datasets: detected type, per-report status and the
// consent questions ("issues") the AI asks about. Pure rules, no AI: counts must never be wrong.
import * as XLSX from 'xlsx'

export const BUCKETS = {
  healthy: { label: 'Passed', tone: 'ok' },
  failed: { label: 'Refresh failed', tone: 'bad' },
  not_configured: { label: 'No scheduled refresh', tone: 'warn' },
  no_rls: { label: 'RLS missing', tone: 'risk' },
  review: { label: 'Needs review', tone: 'info' },
}

export const TYPES = {
  refresh: 'Refresh validation',
  rls: 'RLS validation',
  unknown: 'Unrecognised file',
}

const STALE_DAYS = 7
const key = (s) => String(s).toLowerCase().replace(/[^a-z0-9]/g, '')
const norm = (v) => String(v ?? '').trim().toLowerCase()

// Column aliases, so slightly different headers from Power Automate still work.
const ALIASES = {
  name: ['reportname', 'report', 'datasetname', 'dataset', 'semanticmodel', 'name'],
  enabled: ['refreshenabled', 'scheduledrefresh', 'scheduleenabled'],
  status: ['refreshstatus'],
  error: ['errormessage', 'error', 'errordetails'],
  lastRefresh: ['lastrefresh', 'lastrefreshed', 'lastrefreshtime', 'lastrun'],
  rls: ['rlsimplemented', 'rlsenabled', 'rls'],
  checkedOn: ['checkedon', 'checkeddate', 'validatedon'],
}

function findColumns(headers) {
  const byKey = Object.fromEntries(headers.map((h) => [key(h), h]))
  const cols = {}
  for (const [field, aliases] of Object.entries(ALIASES)) {
    const hit = aliases.find((a) => byKey[a] !== undefined)
    if (hit) cols[field] = byKey[hit]
  }
  return cols
}

export function parseDate(v) {
  if (v instanceof Date) return isNaN(v) ? null : v
  if (!v) return null
  const d = new Date(String(v).replace(',', ''))
  return isNaN(d) ? null : d
}

export const formatValue = (v) =>
  v instanceof Date ? v.toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' }) : String(v ?? '')

// "NZ_Accrual detail Report" -> "NZ"; used for compact chips.
export const shortName = (name) => (name.includes('_') ? name.split('_')[0] : name)

function classify(type, row, cols, now) {
  if (type === 'rls') {
    const v = norm(row[cols.rls])
    if (['yes', 'y', 'true', '1'].includes(v)) return { bucket: 'healthy' }
    if (['no', 'n', 'false', '0'].includes(v)) return { bucket: 'no_rls' }
    return { bucket: 'review' }
  }
  const status = norm(row[cols.status])
  const enabled = norm(row[cols.enabled])
  if (status.includes('fail')) return { bucket: 'failed', error: String(row[cols.error] ?? '').trim() || 'Unknown error' }
  if (status.includes('not configured') || ['no', 'false', 'n'].includes(enabled)) return { bucket: 'not_configured' }
  if (status.includes('complet') || status.includes('success')) {
    const last = parseDate(row[cols.lastRefresh])
    const staleDays = last ? Math.floor((now - last) / 86400000) : null
    return { bucket: 'healthy', staleDays: staleDays >= STALE_DAYS ? staleDays : null }
  }
  return { bucket: 'review' }
}

function buildIssues(type, reports, rows) {
  const of = (b) => reports.filter((r) => r.bucket === b)
  const n = (list, word) => `${list.length} ${word}${list.length === 1 ? '' : 's'}`
  const issues = []

  const failed = of('failed')
  if (failed.length) {
    // One AI call per distinct error message, not per report.
    const groups = Object.values(
      failed.reduce((acc, r) => {
        ;(acc[r.error] ??= { error: r.error, reports: [] }).reports.push(r)
        return acc
      }, {}),
    )
    issues.push({
      id: 'refresh_failed', tone: 'bad', reports: failed, groups,
      title: `${n(failed, 'report')} failed to refresh`,
      question: 'Do you want help fixing each error? The assistant suggests one step at a time and adjusts if it does not work.',
      cta: 'Start troubleshooting',
    })
  }
  const missingRls = of('no_rls')
  if (missingRls.length) issues.push({
    id: 'rls_missing', tone: 'risk', reports: missingRls,
    title: `${n(missingRls, 'report')} without Row-Level Security`,
    question: 'Anyone with access sees all the data. Do you want help implementing Row-Level Security? The assistant will ask how access should work, then guide you step by step.',
    cta: 'Yes, help me implement it',
    ask: {
      label: 'To tailor the steps, describe who should see which data.',
      placeholder: 'Example: Each country team should only see its own country. The table has a Country column (KR, AU, NZ, CN, FR). Users are in groups such as KR-Finance and AU-Finance.',
    },
  })
  const noSchedule = of('not_configured')
  if (noSchedule.length) issues.push({
    id: 'refresh_not_configured', tone: 'warn', reports: noSchedule,
    title: `${n(noSchedule, 'report')} with no scheduled refresh`,
    question: 'Their data only updates when someone refreshes manually. Do you want guided help setting up a scheduled refresh?',
    cta: 'Start guided setup',
  })
  const stale = reports.filter((r) => r.staleDays)
  if (stale.length) issues.push({
    id: 'refresh_stale', tone: 'info', reports: stale, insight: true,
    title: `${n(stale, 'report')} not refreshed in ${Math.min(...stale.map((r) => r.staleDays))}+ days`,
    question: 'Status says Completed, but the data may be outdated. Do you want help finding out why the schedule may have stopped?',
    cta: 'Start troubleshooting',
  })
  if (type === 'unknown') issues.push({
    id: 'general_analysis', tone: 'info', reports: [], rows: rows.slice(0, 50),
    title: 'Unrecognised file type',
    question: 'This file does not match a known validation. Do you want the assistant to analyse it and suggest what needs attention?',
    cta: 'Analyse file',
  })
  return issues
}

export function analyzeSheet({ fileName, sheetName, rows, now = new Date() }) {
  const columns = rows.length ? Object.keys(rows[0]) : []
  const cols = findColumns(columns)
  const type = cols.rls ? 'rls' : cols.status || cols.enabled ? 'refresh' : 'unknown'
  const nameCol = cols.name ?? columns[0]

  const reports = type === 'unknown' ? [] : rows
    .filter((row) => String(row[nameCol] ?? '').trim())
    .map((row) => ({ name: String(row[nameCol]).trim(), row, ...classify(type, row, cols, now) }))

  const counts = Object.fromEntries(Object.keys(BUCKETS).map((b) => [b, reports.filter((r) => r.bucket === b).length]))
  const checkedOn = cols.checkedOn ? parseDate(rows[0]?.[cols.checkedOn]) : null

  return {
    id: `${fileName}::${sheetName}`,
    fileName, sheetName, type, columns, cols, rows, reports, checkedOn,
    summary: { total: type === 'unknown' ? rows.length : reports.length, ...counts },
    issues: buildIssues(type, reports, rows),
  }
}

// Every non-empty sheet becomes a dataset, so one workbook with Refresh + RLS sheets works too.
export async function readFile(file) {
  const wb = XLSX.read(await file.arrayBuffer(), { type: 'array', cellDates: true })
  return wb.SheetNames
    .map((sheetName) => ({ sheetName, rows: XLSX.utils.sheet_to_json(wb.Sheets[sheetName], { defval: '' }) }))
    .filter((s) => s.rows.length)
    .map((s) => analyzeSheet({ fileName: file.name, ...s }))
}
