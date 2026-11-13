// What the assistant is told about the files in a chat, so questions can refer to them.
export function contextOf(datasets) {
  return {
    files: datasets.map((d) => ({
      file: d.fileName,
      file_type: d.type,
      summary: d.summary,
      issues: d.issues.map((i) => ({
        id: i.id, title: i.title, reports: i.reports.map((r) => r.name), errors: i.groups?.map((g) => g.error),
      })),
    })),
  }
}

export function latestDatasets(chat) {
  const last = [...(chat?.messages ?? [])].reverse().find((m) => m.kind === 'analysis')
  return last?.datasets ?? null
}
