import { useState } from 'react'
import { TYPES, formatValue } from '../lib/validation.js'
import SummaryStrip from './SummaryStrip.jsx'
import FindingCard from './FindingCard.jsx'
import ReportTable from './ReportTable.jsx'

const PRIORITY = {
  refresh_failed: 'Refresh failures stop reports from updating.',
  rls_missing: 'Review missing access controls to reduce the risk of exposing data.',
  refresh_not_configured: 'Set up a schedule so reports update automatically.',
  refresh_stale: 'Investigate reports that may be showing outdated data.',
  general_analysis: 'Start by identifying what the file is reporting.',
}

function findingsFor(dataset) {
  const otherFindings = dataset.issues.map((issue) => ({
    title: issue.title,
    errors: issue.groups?.map((group) => group.error),
  }))

  return dataset.issues.flatMap((issue) => {
    const groups = issue.groups ?? [{ error: null, reports: issue.reports }]
    return groups.map((group, index) => {
      const reports = group.reports ?? []
      const title = issue.id === 'refresh_failed'
        ? `${reports.length} ${reports.length === 1 ? 'report failed' : 'reports failed'} with this error`
        : issue.title
      const reportNames = reports.map((report) => report.name).join(', ')
      const prompt = issue.ask
        ? `I want help with ${title}${reportNames ? ` (${reportNames})` : ''}. Please guide me through it.`
        : `Please help me resolve this finding: ${title}${group.error ? ` — ${group.error}` : ''}${reportNames ? ` (${reportNames})` : ''}. Give me a step-by-step solution.`

      return {
        key: `${dataset.id}::${issue.id}::${index}`,
        title,
        prompt,
        issue,
        dataset,
        group,
        context: {
          file_type: dataset.type,
          summary: dataset.summary,
          other_findings: otherFindings,
        },
      }
    })
  })
}

// The assistant's reply to an uploaded file: what was checked, the counts, the findings, and the full report list.
export default function AnalysisMessage({
  datasets, onSelectFinding, selectedFindingKey, completedFindings, selectionDisabled,
}) {
  const [filters, setFilters] = useState({})
  const [showTable, setShowTable] = useState({})

  return datasets.map((d) => {
    const filter = filters[d.id] ?? 'all'
    const known = d.type !== 'unknown'
    const setFilter = (f) => { setFilters((all) => ({ ...all, [d.id]: f })); setShowTable((all) => ({ ...all, [d.id]: true })) }
    return (
      <section key={d.id} className="analysis">
        <p className="lead-in">
          I checked <b>{d.fileName}</b> ({TYPES[d.type].toLowerCase()}, sheet “{d.sheetName}”):{' '}
          {d.summary.total} {known ? 'reports' : 'rows'}
          {d.checkedOn && `, checked ${formatValue(d.checkedOn).split(',').slice(0, 2).join(',')}`}.
        </p>

        <SummaryStrip dataset={d} filter={filter} onFilter={setFilter} />

        <h2 className="block-title">{d.issues.length ? 'What needs attention' : 'Result'}</h2>
        {d.issues.length ? (
          <>
            <p className="block-sub">Choose one finding to work on. The assistant will only start after you send it from the chat box.</p>
            {(() => {
              const allFindings = findingsFor(d)
              const pending = allFindings.filter((finding) => !completedFindings.has(finding.key))
              const recommended = pending[0]
              return (
                <>
                  <div className="findings">
                    {pending.map((finding) => (
                      <FindingCard
                        key={finding.key}
                        finding={finding}
                        selected={finding.key === selectedFindingKey}
                        onSelect={onSelectFinding}
                        disabled={selectionDisabled}
                      />
                    ))}
                  </div>
                  {recommended ? (
                    <aside className="priority-note">
                      <b>Suggested to work on first:</b> {recommended.title}
                      <span>{PRIORITY[recommended.issue.id] ?? 'Review this finding and choose the next action.'}</span>
                      <span>Select an item above, review the message in the chat box, then press Enter to begin.</span>
                    </aside>
                  ) : (
                    <p className="all-reviewed">All findings have been marked as fixed.</p>
                  )}
                </>
              )
            })()}
          </>
        ) : (
          <div className="panel all-clear">No findings. Every report passes.</div>
        )}

        <button className="btn small table-toggle" onClick={() => setShowTable((all) => ({ ...all, [d.id]: !all[d.id] }))}>
          {showTable[d.id] ? 'Hide' : 'Show'} {known ? 'all reports' : 'file contents'}
        </button>
        {showTable[d.id] && <div className="table-block"><ReportTable dataset={d} filter={filter} onFilter={setFilter} /></div>}
      </section>
    )
  })
}
