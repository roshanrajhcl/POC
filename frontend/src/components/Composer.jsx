import { useEffect, useRef, useState } from 'react'
import { APP } from '../config.js'
import Icon from './Icon.jsx'

const ext = (name) => name.split('.').pop().toLowerCase()

// The message box: type, attach files (button or drag and drop), Enter to send, Ctrl+Enter for a new line.
export default function Composer({ onSubmit, busy, large, prefill, disableAttachments = false }) {
  const [text, setText] = useState('')
  const [files, setFiles] = useState([])
  const [error, setError] = useState('')
  const [over, setOver] = useState(false)
  const fileRef = useRef(null)
  const areaRef = useRef(null)

  useEffect(() => {
    if (!prefill) return
    setText(prefill.text)
    if (areaRef.current) {
      areaRef.current.style.height = 'auto'
      areaRef.current.style.height = `${Math.min(areaRef.current.scrollHeight, 220)}px`
      areaRef.current.focus()
    }
  }, [prefill?.id])

  function addFiles(list) {
    if (disableAttachments) return setError('Clear the selected finding before attaching another file.')
    const next = [...files]
    for (const f of list) {
      if (!APP.extensions.includes(ext(f.name))) return setError(`${f.name}: only Excel (.xlsx, .xls) or CSV files can be analysed.`)
      if (f.size > APP.maxFileMB * 1024 * 1024) return setError(`${f.name} is larger than ${APP.maxFileMB} MB.`)
      next.push(f)
    }
    if (next.length > APP.maxFiles) return setError(`You can attach up to ${APP.maxFiles} files at a time.`)
    setError('')
    setFiles(next)
  }

  function send() {
    if (busy || (!text.trim() && !files.length)) return
    onSubmit(text.trim(), files)
    setText('')
    setFiles([])
    setError('')
    if (areaRef.current) areaRef.current.style.height = ''
  }

  function onKeyDown(e) {
    if (e.key !== 'Enter' || e.nativeEvent.isComposing) return
    e.preventDefault()
    if (e.ctrlKey || e.metaKey || e.shiftKey) {
      const el = e.currentTarget
      const { selectionStart: a, selectionEnd: b } = el
      setText(text.slice(0, a) + '\n' + text.slice(b))
      requestAnimationFrame(() => { el.selectionStart = el.selectionEnd = a + 1 })
    } else {
      send()
    }
  }

  function grow(e) {
    setText(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = `${Math.min(e.target.scrollHeight, 220)}px`
  }

  return (
    <div className={`composer-block ${large ? 'large' : ''}`}>
      <div
        className={`composer ${over ? 'over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setOver(true) }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); addFiles([...e.dataTransfer.files]) }}
      >
        {files.length > 0 && (
          <ul className="attachments" aria-label="Attached files">
            {files.map((f, i) => (
              <li key={`${f.name}-${i}`} className="file-chip">
                <Icon name="file" size={16} />
                <span>{f.name}</span>
                <button type="button" aria-label={`Remove ${f.name}`} onClick={() => setFiles(files.filter((_, j) => j !== i))}><Icon name="x" size={14} /></button>
              </li>
            ))}
          </ul>
        )}
        <textarea ref={areaRef} rows={large ? 3 : 1} value={text} onChange={grow} onKeyDown={onKeyDown}
          placeholder={APP.placeholder} aria-label="Message" />
        <div className="composer-bar">
          <input ref={fileRef} type="file" className="sr-only" multiple accept=".xlsx,.xls,.csv"
            onChange={(e) => { addFiles([...e.target.files]); e.target.value = '' }} />
          <button type="button" className="round-btn" onClick={() => fileRef.current?.click()} disabled={disableAttachments} aria-label="Attach files" title={disableAttachments ? 'Clear the selected finding to attach a file' : 'Attach files'}>
            <Icon name="plus" size={20} />
          </button>
          <button type="button" className="round-btn send" onClick={send} disabled={busy || (!text.trim() && !files.length)} aria-label="Send" title="Send">
            <Icon name="send" size={20} />
          </button>
        </div>
      </div>
      {error && <p className="composer-error" role="alert">{error}</p>}
      <p className="composer-hint">Excel (.xlsx, .xls) or CSV · up to {APP.maxFiles} files · {APP.maxFileMB} MB per file</p>
    </div>
  )
}
