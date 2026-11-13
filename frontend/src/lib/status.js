// Short text for the backend status shown in the sidebar footer.
export function statusOf(health) {
  const k = health?.knowledge ?? {}
  if (health === null) return { cls: '', text: 'Checking backend…' }
  if (!health.up) return { cls: 'down', text: 'Backend not reachable' }
  if (!health.ai) return { cls: 'down', text: `${health.provider ?? 'AI provider'} key missing` }
  return { cls: 'up', text: `${health.provider ?? 'AI'} · ${health.model} · ${k.documents ?? 0} documents`, title: `Search: ${k.retrieval ?? 'keyword'}` }
}
