import { BUCKETS } from '../lib/validation.js'

const SHOWN = { refresh: ['healthy', 'failed', 'not_configured', 'review'], rls: ['healthy', 'no_rls', 'review'] }

export default function SummaryStrip({ dataset, filter, onFilter }) {
  const { summary, type, rows, columns } = dataset

  if (type === 'unknown') {
    return (
      <div className="stats">
        <div className="stat"><span className="l">Rows</span><span className="n">{rows.length}</span></div>
        <div className="stat"><span className="l">Columns</span><span className="n">{columns.length}</span></div>
      </div>
    )
  }

  const buckets = SHOWN[type].filter((b) => b !== 'review' || summary[b])
  return (
    <div className="stats">
      <div className="stat"><span className="l">Reports checked</span><span className="n">{summary.total}</span></div>
      {buckets.map((b) => (
        <button key={b} className={`stat tone-${BUCKETS[b].tone}`} aria-pressed={filter === b}
          onClick={() => onFilter(filter === b ? 'all' : b)} title="Filter the report list">
          <span className="l"><i className="dot" />{BUCKETS[b].label}</span>
          <span className="n">{summary[b]}</span>
        </button>
      ))}
    </div>
  )
}
