import { useState } from 'react'
import Icon from './Icon.jsx'

const BASIS = {
  knowledge_base: ['From the knowledge base', 'ok'],
  general_knowledge: ['General guidance, please verify', 'info'],
  insufficient_information: ['Needs more information', 'warn'],
}
const LIKELIHOOD = { high: 'Most likely', medium: 'Possible', low: 'Less likely' }

// One beat of the story: a numbered marker on a vertical line, a title, then the content.
function Beat({ n, title, accent, children }) {
  return (
    <section className={`beat ${accent ? 'accent' : ''}`}>
      <span className="marker" aria-hidden="true">{n}</span>
      <div className="beat-body">
        <h4>{title}</h4>
        {children}
      </div>
    </section>
  )
}

// Tells the answer as a short story: what is happening, why, what to do, how to check.
export default function AnswerView({ data }) {
  const [copied, setCopied] = useState(false)
  const [copyError, setCopyError] = useState('')
  const [label, tone] = BASIS[data.basis] ?? BASIS.general_knowledge
  let n = 0

  async function copy() {
    const e = data.escalation
    const text = [e.summary, e.collect.length ? `Please collect:\n${e.collect.map((c) => `- ${c}`).join('\n')}` : ''].filter(Boolean).join('\n\n')
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch { /* clipboard blocked: nothing to do */ }
  }

  async function copyArtifact() {
    try {
      await navigator.clipboard.writeText(data.action.artifact)
      setCopied(true)
      setCopyError('')
      setTimeout(() => setCopied(false), 1600)
    } catch {
      setCopyError('Copy was blocked by the browser. Select the text and copy it manually.')
    }
  }

  return (
    <div className="answer">
      <div className="answer-meta">
        <span className={`badge tone-${tone}`}>{label}</span>
        <span className="muted">{data.confidence.charAt(0).toUpperCase() + data.confidence.slice(1)} confidence</span>
        <span className="muted">Attempt {data.round}</span>
      </div>

      <div className="story">
        {data.diagnosis && (
          <Beat n={++n} title={data.status === 'ask' ? 'What we know so far' : "What's happening"}>
            <p className="lead">{data.diagnosis}</p>
          </Beat>
        )}

        {data.causes.length > 0 && (
          <Beat n={++n} title="Why it likely happened">
            <ul className="why">
              {data.causes.map((c) => (
                <li key={c.cause}>
                  <span className={`pill lk-${c.likelihood}`}>{LIKELIHOOD[c.likelihood]}</span>
                  <span>{c.cause}</span>
                </li>
              ))}
            </ul>
          </Beat>
        )}

        {data.action && (
          <Beat n={++n} title={`What to do: ${data.action.title}`} accent>
            <ol className="steps">{data.action.steps.map((s) => <li key={s}><span>{s}</span></li>)}</ol>
            {data.action.artifact && (
              <div className="implementation-artifact">
                <div className="artifact-head">
                  <b>{data.action.artifact_label || 'Ready-to-apply implementation'}</b>
                  <button className="btn small" onClick={copyArtifact}>{copied ? 'Copied' : 'Copy'}</button>
                </div>
                <pre><code>{data.action.artifact}</code></pre>
                {copyError && <p className="composer-error" role="alert">{copyError}</p>}
                <p className="artifact-note">Review this implementation and apply it in Power BI. Nothing has been changed automatically.</p>
              </div>
            )}
            {data.action.verify && (
              <p className="verify"><Icon name="check" size={16} /><span><b>How to check it worked:</b> {data.action.verify}</span></p>
            )}
          </Beat>
        )}

        {data.escalation && (
          <Beat n={++n} title="Hand this to your Power BI administrator" accent>
            <p className="summary-text">{data.escalation.summary}</p>
            {data.escalation.collect.length > 0 && (
              <>
                <p className="subhead">Collect before sending</p>
                <ul className="collect">{data.escalation.collect.map((c) => <li key={c}>{c}</li>)}</ul>
              </>
            )}
            <button className="btn small" onClick={copy}>{copied ? 'Copied' : 'Copy summary'}</button>
          </Beat>
        )}
      </div>

      {data.sources.length > 0 && (
        <details className="sources">
          <summary>Based on {data.sources.length} source{data.sources.length === 1 ? '' : 's'}</summary>
          <ul>
            {data.sources.map((s) => (
              <li key={s.id}>{s.kind === 'case' ? 'Resolved case' : 'Document'}: {s.title}, {s.section} <span className="muted">({s.relevance} relevance)</span></li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}
