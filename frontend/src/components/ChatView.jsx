import { useEffect, useRef, useState } from 'react'
import { APP } from '../config.js'
import Icon from './Icon.jsx'
import Composer from './Composer.jsx'
import AnalysisMessage from './AnalysisMessage.jsx'
import Troubleshoot from './Troubleshoot.jsx'

const Avatar = () => <span className="avatar sm" aria-hidden="true">{APP.initials}</span>

function Message({
  m, onBackendError, onRetry, onSelectFinding, selectedFindingKey,
  completedFindings, selectionDisabled, onFindingComplete,
}) {
  if (m.role === 'user') {
    return (
      <div className="msg-row user">
        <div className="bubble">
          {m.files.length > 0 && (
            <ul className="attachments">
              {m.files.map((f, i) => <li key={i} className="file-chip"><Icon name="file" size={16} /><span>{f}</span></li>)}
            </ul>
          )}
          {m.text && <p>{m.text}</p>}
        </div>
      </div>
    )
  }

  let body
  if (m.kind === 'analysis') {
    body = (
      <AnalysisMessage
        datasets={m.datasets}
        onBackendError={onBackendError}
        onSelectFinding={onSelectFinding}
        selectedFindingKey={selectedFindingKey}
        completedFindings={completedFindings}
        selectionDisabled={selectionDisabled}
      />
    )
  }
  else if (m.kind === 'troubleshoot') {
    const { finding } = m
    body = (
      <Troubleshoot
        issue={finding.issue}
        dataset={finding.dataset}
        group={finding.group}
        requirement={finding.requirement}
        context={finding.context}
        onBackendError={onBackendError}
        onComplete={() => onFindingComplete(finding.key)}
      />
    )
  }
  else if (m.kind === 'reading') body = <p className="working"><span className="spinner" /> Reading {m.label}…</p>
  else if (m.kind === 'thinking') body = <p className="working"><span className="spinner" /> Looking through the knowledge base…</p>
  else if (m.kind === 'error') {
    body = (
      <div className="inline-error" role="alert">
        <p>{m.text}</p>
        {m.retry && <button className="btn small" onClick={() => onRetry(m.id, m.retry)}>Try again</button>}
      </div>
    )
  } else {
    body = (
      <>
        <p className="answer-text">{m.text}</p>
        {m.sources?.length > 0 && <p className="answer-src">Sources: {m.sources.map((s) => s.title).join(' · ')}</p>}
        {m.basis === 'general_knowledge' && <p className="answer-src">Not found in the knowledge base. This is general guidance, please verify.</p>}
      </>
    )
  }

  return (
    <div className="msg-row assistant">
      <Avatar />
      <div className="assistant-body">{body}</div>
    </div>
  )
}

export default function ChatView({ chat, hidden, onSubmit, onRetry, onBackendError }) {
  const endRef = useRef(null)
  const prefillId = useRef(0)
  const [selectedFinding, setSelectedFinding] = useState(null)
  const [prefill, setPrefill] = useState(null)
  const [completedFindings, setCompletedFindings] = useState(() => new Set())
  const [activeFinding, setActiveFinding] = useState(false)
  const last = chat.messages[chat.messages.length - 1]
  const busy = activeFinding || last?.kind === 'reading' || last?.kind === 'thinking'

  function selectFinding(finding) {
    setSelectedFinding(finding)
    setPrefill({ id: ++prefillId.current, text: finding.prompt })
  }

  function clearSelection() {
    setSelectedFinding(null)
    setPrefill({ id: ++prefillId.current, text: '' })
  }

  function submit(text, files) {
    const finding = files.length ? null : selectedFinding
    if (finding) setActiveFinding(true)
    setSelectedFinding(null)
    setPrefill({ id: ++prefillId.current, text: '' })
    onSubmit(chat.id, text, files, finding)
  }

  function completeFinding(key) {
    setCompletedFindings((current) => new Set(current).add(key))
    setActiveFinding(false)
  }

  useEffect(() => { endRef.current?.scrollIntoView({ block: 'end', behavior: 'smooth' }) }, [chat.messages.length, last?.kind])

  return (
    <div className="chat" hidden={hidden}>
      <div className="scroll">
        <div className="column">
          {chat.messages.map((m) => (
            <Message
              key={m.id}
              m={m}
              onBackendError={onBackendError}
              onRetry={(id, q) => onRetry(chat.id, id, q)}
              onSelectFinding={selectFinding}
              selectedFindingKey={selectedFinding?.key}
              completedFindings={completedFindings}
              selectionDisabled={activeFinding}
              onFindingComplete={completeFinding}
            />
          ))}
          <div ref={endRef} />
        </div>
      </div>
      <div className="composer-wrap">
        {selectedFinding && (
          <div className="selected-finding">
            <span>Selected to work on: <b>{selectedFinding.title}</b></span>
            <button type="button" className="btn quiet small" onClick={clearSelection}>Clear</button>
          </div>
        )}
        <Composer
          busy={busy}
          prefill={prefill}
          disableAttachments={Boolean(selectedFinding)}
          onSubmit={submit}
        />
      </div>
    </div>
  )
}
