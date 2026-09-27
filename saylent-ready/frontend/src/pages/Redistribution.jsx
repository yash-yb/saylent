import { useEffect, useState } from 'react'
import { api } from '../api'
import StatusBadge from '../components/StatusBadge'
import { LoadingState, ErrorState } from './Dashboard'
import { ArrowRight, Check, X } from 'lucide-react'

export default function Redistribution() {
  const [recs, setRecs] = useState(null)
  const [error, setError] = useState(null)

  const load = () => api.redistribution('pending').then(setRecs).catch((e) => setError(e.message))
  useEffect(() => { load() }, [])

  if (error) return <ErrorState message={error} />
  if (!recs) return <LoadingState />

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-white">Redistribution Recommendations</h1>
        <p className="text-sm text-slate-400 mt-1">
          AI-recommended cross-district transfers, computed from forecast surplus vs. projected shortfall
        </p>
      </header>

      <div className="space-y-3">
        {recs.map((r) => (
          <div key={r.id} className="card flex items-center justify-between gap-4">
            <div className="flex-1">
              <p className="text-xs text-slate-500 mb-1">{r.medicine_name}</p>
              <div className="flex items-center gap-3 text-sm">
                <div>
                  <p className="text-white font-medium">{r.from_phc}</p>
                  <p className="text-slate-500 text-xs">{r.from_district}</p>
                </div>
                <div className="flex flex-col items-center px-2">
                  <ArrowRight size={16} className="text-accent-cyan" />
                  <span className="text-[11px] text-accent-cyan font-semibold">{r.suggested_qty}</span>
                </div>
                <div>
                  <p className="text-white font-medium">{r.to_phc}</p>
                  <p className="text-slate-500 text-xs">{r.to_district}</p>
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-2">{r.reason}</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <StatusBadge status={r.status} />
              <button onClick={() => api.approveRedistribution(r.id).then(load)}
                className="p-2 rounded-lg border border-base-700 hover:border-accent-emerald/50 hover:text-accent-emerald text-slate-400">
                <Check size={15} />
              </button>
              <button onClick={() => api.rejectRedistribution(r.id).then(load)}
                className="p-2 rounded-lg border border-base-700 hover:border-accent-rose/50 hover:text-accent-rose text-slate-400">
                <X size={15} />
              </button>
            </div>
          </div>
        ))}
        {recs.length === 0 && <p className="text-slate-500 text-sm">No pending recommendations — network is balanced.</p>}
      </div>
    </div>
  )
}
