export default function StatCard({ label, value, sub, tone = 'default', icon: Icon }) {
  const toneMap = {
    default: 'text-white',
    danger: 'text-accent-rose',
    warning: 'text-accent-amber',
    good: 'text-accent-emerald',
    info: 'text-accent-cyan',
  }
  return (
    <div className="card flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">{label}</span>
        {Icon && <Icon size={16} className="text-slate-500" />}
      </div>
      <span className={`text-3xl font-extrabold ${toneMap[tone]}`}>{value}</span>
      {sub && <span className="text-xs text-slate-500">{sub}</span>}
    </div>
  )
}
