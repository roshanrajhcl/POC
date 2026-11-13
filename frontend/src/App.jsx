import { useCallback, useEffect, useRef, useState } from 'react'
import { APP } from './config.js'
import { readFile } from './lib/validation.js'
import { askQuestion, checkHealth } from './lib/api.js'
import { contextOf, latestDatasets } from './lib/context.js'
import Sidebar from './components/Sidebar.jsx'
import Welcome from './components/Welcome.jsx'
import ChatView from './components/ChatView.jsx'
import Icon from './components/Icon.jsx'

let counter = 0
const uid = () => `${Date.now().toString(36)}-${counter++}`

export default function App() {
  const [chats, setChats] = useState([])        // { id, title, messages[] }, newest first
  const [activeId, setActiveId] = useState(null) // null shows the welcome screen
  const [health, setHealth] = useState(null)
  const [navOpen, setNavOpen] = useState(false)
  const chatsRef = useRef(chats)
  chatsRef.current = chats

  const refreshHealth = useCallback(() => { checkHealth().then(setHealth) }, [])
  useEffect(refreshHealth, [refreshHealth])

  const patch = (chatId, fn) => setChats((cs) => cs.map((c) => (c.id === chatId ? { ...c, messages: fn(c.messages) } : c)))
  const add = (chatId, msg) => patch(chatId, (m) => [...m, msg])
  const replace = (chatId, id, msg) => patch(chatId, (m) => m.map((x) => (x.id === id ? { ...msg, id } : x)))

  // Answers a free-text question from the knowledge base. `replaceId` swaps an error message for a retry.
  async function ask(chatId, question, datasets, replaceId) {
    const id = replaceId ?? uid()
    const thinking = { role: 'assistant', kind: 'thinking' }
    if (replaceId) replace(chatId, id, thinking)
    else add(chatId, { ...thinking, id })
    const source = datasets ?? latestDatasets(chatsRef.current.find((c) => c.id === chatId))
    try {
      const res = await askQuestion(question, source ? contextOf(source) : null)
      replace(chatId, id, { role: 'assistant', kind: 'answer', text: res.answer, sources: res.sources, basis: res.basis })
    } catch (e) {
      replace(chatId, id, { role: 'assistant', kind: 'error', text: e.message, retry: question })
      refreshHealth()
    }
  }

  async function submit(chatId, text, files, finding = null) {
    let id = chatId
    if (!id) {
      id = uid()
      const title = files[0]?.name ?? (text.length > 48 ? `${text.slice(0, 48)}…` : text)
      setChats((cs) => [{ id, title, messages: [] }, ...cs])
      setActiveId(id)
    }
    add(id, { id: uid(), role: 'user', text, files: files.map((f) => f.name) })

    if (finding) {
      add(id, {
        id: uid(),
        role: 'assistant',
        kind: 'troubleshoot',
        finding: { ...finding, requirement: text },
      })
      return
    }

    let datasets = null
    if (files.length) {
      const rid = uid()
      add(id, { id: rid, role: 'assistant', kind: 'reading', label: files.map((f) => f.name).join(', ') })
      try {
        const result = (await Promise.all(files.map(readFile))).flat()
        if (!result.length) throw new Error('That file has no rows to check.')
        datasets = result
        replace(id, rid, { role: 'assistant', kind: 'analysis', datasets })
      } catch (e) {
        replace(id, rid, { role: 'assistant', kind: 'error', text: `Could not read that file: ${e.message}` })
      }
    }
    if (text) await ask(id, text, datasets)
  }

  const remove = (id) => {
    setChats((cs) => cs.filter((c) => c.id !== id))
    if (id === activeId) setActiveId(null)
  }
  const select = (id) => { setActiveId(id); setNavOpen(false) }
  const fresh = () => { setActiveId(null); setNavOpen(false) }

  return (
    <div className="shell">
      <Sidebar chats={chats} activeId={activeId} health={health} open={navOpen} onClose={() => setNavOpen(false)}
        onNew={fresh} onSelect={select} onDelete={remove} />

      <main className="main">
        <header className="topbar">
          <button className="icon-btn menu" onClick={() => setNavOpen(true)} aria-label="Open menu"><Icon name="menu" /></button>
          <span className="avatar xs" aria-hidden="true">{APP.initials}</span>
          <span className="top-title">{APP.name}</span>
        </header>

        {activeId === null && <Welcome onSubmit={(t, f) => submit(null, t, f)} />}

        {/* Every chat stays mounted so troubleshooting conversations survive switching chats. */}
        {chats.map((c) => (
          <ChatView key={c.id} chat={c} hidden={c.id !== activeId} onSubmit={submit}
            onRetry={(chatId, msgId, q) => ask(chatId, q, null, msgId)} onBackendError={refreshHealth} />
        ))}
      </main>
    </div>
  )
}
