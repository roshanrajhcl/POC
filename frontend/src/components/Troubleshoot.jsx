import { useEffect, useRef, useState } from 'react'
import { saveCase, troubleshoot } from '../lib/api.js'
import AnswerView from './AnswerView.jsx'
import ReplyBar from './ReplyBar.jsx'

// One troubleshooting conversation. The backend keeps no session, so every round sends the whole history.
export default function Troubleshoot({ issue, dataset, group, requirement, context, onBackendError, onComplete }) {
  const [turns, setTurns] = useState([])     // sent to the backend
  const [thread, setThread] = useState([])   // shown: { kind: 'ai', data } | { kind: 'user', label }
  const [state, setState] = useState('loading') // loading | ready | error | resolved
  const [error, setError] = useState('')
  const retry = useRef(null)
  const started = useRef(false)

  const base = {
    issue: issue.id,
    file_type: dataset.type,
    ...(group.error && { error: group.error }),
    reports: group.reports.map((r) => r.name),
    rows: issue.rows ?? group.reports.map((r) => r.row),
    context,
  }

  async function round(nextTurns, label) {
    retry.current = () => round(nextTurns, label)
    setState('loading')
    setError('')
    try {
      const data = await troubleshoot({ ...base, turns: nextTurns })
      const added = data.action ? [{
        type: 'suggestion',
        title: data.action.title,
        steps: data.action.steps,
        ...(data.action.artifact && { artifact_label: data.action.artifact_label, artifact: data.action.artifact }),
      }] : []
      setTurns([...nextTurns, ...added])
      setThread((t) => [...t, ...(label ? [{ kind: 'user', label }] : []), { kind: 'ai', data }])
      setState('ready')
    } catch (e) {
      setError(e.message)
      setState('error')
      onBackendError()
    }
  }

  useEffect(() => {
    if (started.current) return
    started.current = true
    round(requirement ? [{ type: 'message', text: requirement }] : [], null)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const feedback = (outcome, note, label) => round([...turns, { type: 'feedback', outcome, ...(note && { note }) }], label)
  const answers = (items) => round([...turns, { type: 'answers', items }], items.map((i) => i.answer).join(', '))
  const prepareFix = () => round([
    ...turns,
    { type: 'prepare_fix', text: 'Prepare a ready-to-apply implementation for the current fix. Include the exact artifact and where to apply it. Do not claim to change Power BI.' },
  ], 'Prepare a ready-to-apply fix')

  async function worked(note) {
    setState('loading')
    try {
      await saveCase({ issue: issue.id, ...(group.error && { error: group.error }), reports: base.reports, turns, resolution: note })
      setState('resolved')
      onComplete()
    } catch (e) {
      setError(e.message)
      setState('error')
      retry.current = () => worked(note)
    }
  }

  const last = [...thread].reverse().find((e) => e.kind === 'ai')
  const past = thread.slice(0, thread.lastIndexOf(last))

  return (
    <div className="thread">
      {group.error && <p className="target"><code>{group.error}</code><span>{group.reports.map((r) => r.name).join(', ')}</span></p>}
      {requirement && <p className="requirement"><b>Your requirement:</b> {requirement}</p>}

      {past.length > 0 && (
        <ol className="history" aria-label="Conversation so far">
          {past.map((e, i) => e.kind === 'user'
            ? <li key={i} className="you">You: {e.label}</li>
            : <li key={i}>{e.data.action ? `Suggested: ${e.data.action.title}` : e.data.status === 'ask' ? 'Asked questions' : 'Escalated'}</li>)}
        </ol>
      )}

      {last && state !== 'resolved' && (
        <div className="assistant-card">
          <AnswerView data={last.data} />
        </div>
      )}
      {state === 'loading' && <p className="working" role="status"><span className="spinner" /> {last ? 'Thinking about what to try next…' : 'Looking through the knowledge base…'}</p>}
      {state === 'error' && (
        <>
          <p className="inline-error" role="alert">{error}</p>
          <div className="actions"><button className="btn primary small" onClick={() => retry.current?.()}>Try again</button></div>
        </>
      )}
      {state === 'ready' && last && <ReplyBar data={last.data} onFeedback={feedback} onAnswers={answers} onWorked={worked} onPrepareFix={prepareFix} />}
      {state === 'resolved' && (
        <p className="resolved">Marked as fixed. The case is saved for review. Once approved, the assistant can use it for similar errors.</p>
      )}
    </div>
  )
}
