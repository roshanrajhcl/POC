// Self-check for the validation rules: `npm test`
import assert from 'node:assert/strict'
import { analyzeSheet } from '../src/lib/validation.js'
import { REFRESH_SAMPLE, RLS_SAMPLE } from './fixtures.js'

const now = new Date('2026-11-13T12:00:00')

const refresh = analyzeSheet({ fileName: 'refresh.xlsx', sheetName: 'Sheet1', rows: REFRESH_SAMPLE, now })
assert.equal(refresh.type, 'refresh')
assert.deepEqual(
  [refresh.summary.total, refresh.summary.healthy, refresh.summary.failed, refresh.summary.not_configured],
  [9, 3, 2, 4],
)
assert.deepEqual(refresh.issues.map((i) => i.id), ['refresh_failed', 'refresh_not_configured', 'refresh_stale'])
assert.deepEqual(refresh.issues[0].groups.map((g) => g.error), ['Timeout error', 'An error occurred while processing'])
assert.equal(refresh.issues[2].reports.length, 3) // KR, AU, FR last refreshed 19+ days ago

const rls = analyzeSheet({ fileName: 'rls.xlsx', sheetName: 'Sheet1', rows: RLS_SAMPLE, now })
assert.equal(rls.type, 'rls')
assert.deepEqual([rls.summary.healthy, rls.summary.no_rls], [4, 5])
assert.deepEqual(rls.issues.map((i) => i.id), ['rls_missing'])

const other = analyzeSheet({ fileName: 'x.csv', sheetName: 'x', rows: [{ Owner: 'a', Size: 3 }], now })
assert.equal(other.type, 'unknown')
assert.deepEqual(other.issues.map((i) => i.id), ['general_analysis'])

console.log('validation self-check passed')
