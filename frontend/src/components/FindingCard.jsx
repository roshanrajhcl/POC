import { shortName } from '../lib/validation.js'
import Icon, { TONE_ICON } from './Icon.jsx'

export default function FindingCard({ finding, selected, onSelect, disabled }) {
  const { issue, group } = finding
  const reports = group.reports ?? []

  return (
    <article className="panel finding-row">
      <span className={`finding-icon tone-${issue.tone}`}>
        <Icon name={TONE_ICON[issue.tone] ?? 'info'} />
      </span>
      <div className="finding-row-content">
        <h3>{finding.title}</h3>
        {group.error && <code className="finding-error">{group.error}</code>}
        {reports.length > 0 && (
          <div className="chips" aria-label="Affected reports">
            {reports.map((report) => (
              <span key={report.name} className="chip-report" title={report.name}>{shortName(report.name)}</span>
            ))}
          </div>
        )}
      </div>
      <button
        className={`btn small ${selected ? '' : 'primary'}`}
        type="button"
        aria-pressed={selected}
        disabled={disabled}
        onClick={() => onSelect(finding)}
      >
        {selected ? 'Selected' : 'Select'}
      </button>
    </article>
  )
}
