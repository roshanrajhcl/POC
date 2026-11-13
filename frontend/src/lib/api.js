// Calls the backend. The key and the AI live there; the browser never sees them.
// Contract: see "API" in README.md at the project root.
const BASE = import.meta.env.VITE_API_BASE ?? '/api'

async function request(path, options = {}, timeout = 90000) {
  let res
  try {
    res = await fetch(`${BASE}${path}`, { ...options, signal: AbortSignal.timeout(timeout) })
  } catch {
    throw new Error('The backend is not reachable. Start it, then try again.')
  }
  if (!res.ok) {
    let message = `The backend returned an error (${res.status}). Try again.`
    try {
      const d = await res.json()
      if (d?.detail?.message) message = d.detail.message
      else if (typeof d?.detail === 'string') message = d.detail
    } catch { /* keep the generic message */ }
    throw new Error(message)
  }
  return res.json()
}

const post = (path, body) =>
  request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

// { up, ai, provider, model, embeddingModel, knowledge: { documents, chunks, cases, retrieval } }
export async function checkHealth() {
  try {
    const d = await request('/health', {}, 2500)
    return { up: true, ai: Boolean(d.ai), provider: d.provider ?? null, model: d.model ?? null, embeddingModel: d.embedding_model ?? null, knowledge: d.knowledge ?? {} }
  } catch {
    return { up: false, ai: false }
  }
}

// One round of the troubleshooting conversation.
// req: { issue, file_type, error?, reports[], rows[], turns[], context? }
export const troubleshoot = (req) => post('/troubleshoot', req)

// Saves a resolved case. It is only used for learning after a person approves it.
export const saveCase = (c) => post('/cases', c)

export async function askQuestion(question, context) {
  const d = await post('/chat', { question, context })
  return { answer: String(d.answer ?? ''), sources: d.sources ?? [], basis: d.basis }
}
