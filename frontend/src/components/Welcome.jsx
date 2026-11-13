import { APP } from '../config.js'
import Composer from './Composer.jsx'

const CHECKS = [
  ['Refresh failed', 'Refresh status is Failed. Grouped by error message.'],
  ['No scheduled refresh', 'Status is Not Configured, or Refresh Enabled is No.'],
  ['Stale data', 'Completed, but the last refresh is 7 or more days old.'],
  ['Row-Level Security (RLS) missing', 'RLS_Implemented is no.'],
]

export default function Welcome({ onSubmit }) {
  return (
    <div className="welcome">
      <span className="avatar xl" aria-hidden="true">{APP.initials}</span>
      <h1>{APP.name}</h1>
      <p className="subtitle">{APP.subtitle}</p>

      <Composer large onSubmit={onSubmit} />

      <div className="suggest-row">
        {APP.suggestions.map((s) => <button key={s} className="suggest-chip" onClick={() => onSubmit(s, [])}>{s}</button>)}
      </div>

      <details className="what">
        <summary>What does it check in a validation file?</summary>
        <ul>{CHECKS.map(([n, r]) => <li key={n}><b>{n}</b>: {r}</li>)}</ul>
        <p>The file is read in your browser. Only the rows with problems are sent to the backend, and only after you approve each fix.</p>
      </details>
    </div>
  )
}
