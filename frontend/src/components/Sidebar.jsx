import { useState } from 'react'
import { APP } from '../config.js'
import { statusOf } from '../lib/status.js'
import Icon from './Icon.jsx'

export default function Sidebar({ chats, activeId, health, open, onClose, onNew, onSelect, onDelete }) {
  const [q, setQ] = useState('')
  const shown = chats.filter((c) => c.title.toLowerCase().includes(q.trim().toLowerCase()))
  const status = statusOf(health)

  return (
    <>
      {open && <div className="scrim" onClick={onClose} />}
      <aside className={`sidebar ${open ? 'open' : ''}`} aria-label="Chats">
        <div className="side-brand">
          <span className="logo" aria-hidden="true"><i /><i /><i /></span>
          <b>{APP.brand}</b>
        </div>

        <button className="side-item" onClick={onNew}><Icon name="newchat" size={18} /> New chat</button>
        <label className="side-search">
          <Icon name="search" size={16} />
          <input type="search" placeholder="Search chats" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search chats" />
        </label>

        <p className="side-label">Agent</p>
        <button className="side-item agent" onClick={onNew} title="Start a new chat with this assistant">
          <span className="avatar sm" aria-hidden="true">{APP.initials}</span>
          <span className="ellipsis">{APP.name}</span>
        </button>

        <p className="side-label">This session</p>
        <ul className="chat-list">
          {shown.map((c) => (
            <li key={c.id} className={c.id === activeId ? 'active' : ''}>
              <button className="chat-link" onClick={() => onSelect(c.id)} title={c.title}><span className="ellipsis">{c.title}</span></button>
              <button className="chat-del" onClick={() => onDelete(c.id)} aria-label={`Delete chat ${c.title}`}><Icon name="x" size={14} /></button>
            </li>
          ))}
          {!shown.length && <li className="empty">{chats.length ? 'No chats match.' : 'No chats yet.'}</li>}
        </ul>

        <div className="side-foot">
          <span className={`backend ${status.cls}`} role="status" title={status.title}>{status.text}</span>
        </div>
      </aside>
    </>
  )
}
