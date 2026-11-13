import { useState } from 'react'
import { BUCKETS, formatValue } from '../lib/validation.js'
import StatusBadge from './StatusBadge.jsx'

const dash = <span className="muted">-</span>

export default function ReportTable({ dataset, filter, onFilter }) {
  const [query, setQuery] = useState('')
  const { type, reports, cols, columns, rows, summary } = dataset

  if (type === 'unknown') {
    return (
      <div className="panel table-wrap">
        <table>
          <thead><tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
          <tbody>
            {rows.slice(0, 100).map((row, i) => (
              <tr key={i}>{columns.map((c) => <td key={c}>{formatValue(row[c])}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  const details = type === 'refresh'
    ? [
        ['Refresh enabled', (r) => formatValue(r.row[cols.enabled]) || dash],
        ['Error message', (r) => (r.error ? <code className="err">{r.error}</code> : dash)],
        ['Last refresh', (r) => (
          <>
            {formatValue(r.row[cols.lastRefresh]) || dash}
            {r.staleDays && <span className="stale">{r.staleDays} days ago</span>}
          </>
        )],
      ]
    : [
        ['RLS implemented', (r) => formatValue(r.row[cols.rls])],
        ['Checked on', (r) => formatValue(r.row[cols.checkedOn]) || dash],
      ]

  const present = Object.keys(BUCKETS).filter((b) => summary[b])
  const shown = reports.filter(
    (r) => (filter === 'all' || r.bucket === filter) && r.name.toLowerCase().includes(query.trim().toLowerCase()),
  )

  return (
    <div className="panel">
      <div className="tools">
        <label>Status
          <select value={filter} onChange={(e) => onFilter(e.target.value)}>
            <option value="all">All ({reports.length})</option>
            {present.map((b) => <option key={b} value={b}>{BUCKETS[b].label} ({summary[b]})</option>)}
          </select>
        </label>
        <label className="sr-only" htmlFor="report-search">Search reports</label>
        <input id="report-search" type="search" placeholder="Search reports" value={query} onChange={(e) => setQuery(e.target.value)} />
        <span className="count">{shown.length} of {reports.length} shown</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Report</th><th>Status</th>{details.map(([h]) => <th key={h}>{h}</th>)}</tr>
          </thead>
          <tbody>
            {shown.map((r, i) => (
              <tr key={`${r.name}-${i}`}>
                <td>{r.name}</td>
                <td><StatusBadge bucket={r.bucket} /></td>
                {details.map(([h, cell]) => <td key={h}>{cell(r)}</td>)}
              </tr>
            ))}
            {!shown.length && <tr><td colSpan={details.length + 2} className="empty">No reports match.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
