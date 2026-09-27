const STYLES = {
  healthy: 'bg-emerald-500/15 text-emerald-400',
  good: 'bg-emerald-500/15 text-emerald-400',
  watch: 'bg-amber-500/15 text-amber-400',
  low: 'bg-amber-500/15 text-amber-400',
  medium: 'bg-amber-500/15 text-amber-400',
  critical: 'bg-rose-500/15 text-rose-400',
  high: 'bg-rose-500/15 text-rose-400',
  pending: 'bg-indigo-500/15 text-indigo-300',
  approved: 'bg-emerald-500/15 text-emerald-400',
  rejected: 'bg-slate-500/15 text-slate-400',
}

export default function StatusBadge({ status }) {
  const cls = STYLES[status] || 'bg-slate-500/15 text-slate-400'
  return <span className={`badge ${cls} capitalize`}>{status}</span>
}
