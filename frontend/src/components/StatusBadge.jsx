import { BUCKETS } from '../lib/validation.js'

export default function StatusBadge({ bucket }) {
  const { label, tone } = BUCKETS[bucket]
  return <span className={`badge tone-${tone}`}>{label}</span>
}
