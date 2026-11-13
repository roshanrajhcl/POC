// Small outline icons, drawn inline so the page needs no icon library.
const PATHS = {
  alert: <><circle cx="12" cy="12" r="9" /><path d="M12 7.5v5.5M12 16.5v.01" /></>,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  shield: <path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6l7-3z" />,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5.5M12 7.5v.01" /></>,
  upload: <path d="M12 16V5m0 0l-4 4m4-4l4 4M5 19h14" />,
  check: <path d="M5 12.5l4.5 4.5L19 7.5" />,
  file: <><path d="M7 3h7l4 4v14H7z" /><path d="M14 3v4h4M10 13h5M10 17h5" /></>,
  newchat: <><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4 12.5-12.5z" /></>,
  search: <><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></>,
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  plus: <path d="M12 5v14M5 12h14" />,
  send: <path d="M12 19V5m0 0l-6 6m6-6l6 6" />,
  x: <path d="M6 6l12 12M18 6L6 18" />,
}

export const TONE_ICON = { bad: 'alert', warn: 'clock', risk: 'shield', info: 'info', ok: 'check' }

export default function Icon({ name, size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      {PATHS[name] ?? PATHS.info}
    </svg>
  )
}
