import { useState } from 'react'

const FORMS = {
  worked: { label: 'What fixed it? (optional, helps the next person)', required: false, send: 'Save and finish' },
  cant: { label: 'What stopped you? (optional)', required: false, send: 'Send' },
  different: { label: 'Paste the new error message or describe what you see now', required: true, send: 'Send' },
  details: { label: 'Add anything you noticed, such as how long it ran or the full error text', required: true, send: 'Send' },
}

// What the user can do after each answer. The choice goes back to the assistant as the next turn.
export default function ReplyBar({ data, onFeedback, onAnswers, onWorked }) {
  const [form, setForm] = useState(null)   // worked | cant | different | details
  const [text, setText] = useState('')
  const [showAccessNotice, setShowAccessNotice] = useState(false)

  if (data.status === 'ask') return <Questions questions={data.questions} onSubmit={onAnswers} />

  const open = (f) => { setForm(f); setText('') }
  const submit = (e) => {
    e.preventDefault()
    const note = text.trim()
    if (form === 'worked') return onWorked(note)
    const map = {
      cant: ['cant_do', 'I could not do this step'],
      different: ['different_error', 'Different error now'],
      details: ['info', 'Added details'],
    }
    const [outcome, label] = map[form]
    onFeedback(outcome, note, label)
  }

  return (
    <div className="reply">
      {data.status === 'suggest' && <p className="reply-title">Did this fix it?</p>}
      {data.status === 'escalate' && <p className="reply-title">Learned something new, or fixed it another way?</p>}
      <div className="actions wrap">
        <button className="btn success small" onClick={() => open('worked')}>It worked</button>
        {data.status === 'suggest' && (
          <>
            <button className="btn small" onClick={() => onFeedback('still_failing', '', 'Tried it, still failing')}>Still failing</button>
            <button className="btn small" onClick={() => open('cant')}>I can't do this step</button>
            <button className="btn small" onClick={() => open('different')}>Different error now</button>
            <button className="btn small" onClick={() => setShowAccessNotice(true)}>Do you want me to fix directly?</button>
          </>
        )}
        <button className="btn quiet small" onClick={() => open('details')}>Add details</button>
      </div>

      {showAccessNotice && <p className="artifact-note" role="status">I don't have access to Power BI, so I can't make changes directly.</p>}

      {form && (
        <form className="reply-form" onSubmit={submit}>
          <label htmlFor="reply-text">{FORMS[form].label}</label>
          <textarea id="reply-text" rows={3} maxLength={1900} value={text} autoFocus onChange={(e) => setText(e.target.value)} />
          <div className="actions">
            <button className="btn primary small" disabled={FORMS[form].required && !text.trim()}>{FORMS[form].send}</button>
            <button type="button" className="btn quiet small" onClick={() => setForm(null)}>Cancel</button>
          </div>
        </form>
      )}
    </div>
  )
}

function Questions({ questions, onSubmit }) {
  const [picked, setPicked] = useState({})   // question index -> chosen option
  const [other, setOther] = useState({})     // question index -> typed answer
  const answer = (i) => (picked[i] === 'Other' ? (other[i] ?? '').trim() : picked[i])
  const complete = questions.every((_, i) => answer(i))

  return (
    <form className="reply questions" onSubmit={(e) => {
      e.preventDefault()
      onSubmit(questions.map((q, i) => ({ question: q.text, answer: answer(i) })))
    }}>
      <p className="reply-title">A few questions to narrow this down</p>
      {questions.map((q, i) => (
        <fieldset key={q.text}>
          <legend>{q.text}</legend>
          {[...q.options, 'Other', "I don't know"].filter((o, j, all) => all.indexOf(o) === j).map((o) => (
            <label key={o} className="option">
              <input type="radio" name={`q${i}`} checked={picked[i] === o} onChange={() => setPicked({ ...picked, [i]: o })} /> {o}
            </label>
          ))}
          {picked[i] === 'Other' && (
            <input className="other" type="text" placeholder="Type your answer" maxLength={400} autoFocus
              value={other[i] ?? ''} onChange={(e) => setOther({ ...other, [i]: e.target.value })} />
          )}
        </fieldset>
      ))}
      <div className="actions"><button className="btn primary small" disabled={!complete}>Send answers</button></div>
    </form>
  )
}
