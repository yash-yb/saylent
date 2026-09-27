import { useEffect, useState } from 'react'
import { api } from '../api'
import StatusBadge from '../components/StatusBadge'
import { LoadingState, ErrorState } from './Dashboard'
import { CheckCircle2 } from 'lucide-react'

const TYPE_LABEL = {
  stockout_risk: 'Stockout Risk',
  low_bed_capacity: 'Bed Capacity',
  low_attendance: 'Staff Attendance',
}

export default function Alerts() {
  const [alerts, setAlerts] = useState(null)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all')

  const load = () => api.alerts().then(setAlerts).catch((e) => setError(e.message))
  useEffect(() => { load() }, [])

  if (error) return <ErrorState message={error} />
  if (!alerts) return <LoadingState />

  const filtered = filter === 'all' ? alerts : alerts.filter((a) => a.severity === filter)

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Alerts</h1>
          <p className="text-sm text-slate-400 mt-1">{alerts.length} active alerts across the network</p>
        </div>
        <div className="flex gap-2">
          {['all', 'critical', 'high', 'medium'].map((f) => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize border ${
                filter === f ? 'bg-accent-indigo/20 border-accent-indigo/40 text-accent-cyan' : 'border-base-700 text-slate-400 hover:text-white'
              }`}>
              {f}
            </button>
          ))}
        </div>
      </header>

      <div className="space-y-3">
        {filtered.map((a) => (
          <div key={a.id} className="card flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <StatusBadge status={a.severity} />
                <span className="text-xs text-slate-500">{TYPE_LABEL[a.type] || a.type}</span>
              </div>
              <p className="text-sm text-white font-medium">{a.phc_name} · {a.district_name}</p>
              <p className="text-sm text-slate-400 mt-1">{a.message}</p>
            </div>
            <button
              onClick={() => api.resolveAlert(a.id).then(load)}
              className="shrink-0 flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-accent-emerald border border-base-700 hover:border-accent-emerald/40 rounded-lg px-3 py-1.5 transition-colors"
            >
              <CheckCircle2 size={14} /> Resolve
            </button>
          </div>
        ))}
        {filtered.length === 0 && <p className="text-slate-500 text-sm">No alerts match this filter.</p>}
      </div>
    </div>
  )
}
