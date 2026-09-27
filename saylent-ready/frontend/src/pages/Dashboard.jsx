import { useEffect, useState } from 'react'
import { BedDouble, ShieldAlert, PackageX, ArrowLeftRight } from 'lucide-react'
import { api } from '../api'
import StatCard from '../components/StatCard'
import StatusBadge from '../components/StatusBadge'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [districts, setDistricts] = useState([])
  const [alerts, setAlerts] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([api.nationalSummary(), api.districtScores(), api.alerts({ severity: 'critical' })])
      .then(([s, d, a]) => {
        setSummary(s)
        setDistricts(d)
        setAlerts(a.slice(0, 5))
      })
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <ErrorState message={error} />
  if (!summary) return <LoadingState />

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-white">National Overview</h1>
        <p className="text-sm text-slate-400 mt-1">
          Live resilience snapshot across {summary.total_districts} districts and {summary.total_phcs} PHCs
        </p>
      </header>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Bed Occupancy" value={`${summary.bed_occupancy_pct}%`}
          sub={`${summary.occupied_beds}/${summary.total_beds} beds in use`} icon={BedDouble}
          tone={summary.bed_occupancy_pct > 85 ? 'danger' : 'info'} />
        <StatCard label="Active Alerts" value={summary.active_alerts}
          sub={`${summary.critical_alerts} critical`} icon={ShieldAlert}
          tone={summary.critical_alerts > 0 ? 'danger' : 'good'} />
        <StatCard label="Medicines at Risk" value={summary.medicines_at_risk}
          sub="Projected stockout within lead time" icon={PackageX} tone="warning" />
        <StatCard label="Pending Redistributions" value={summary.pending_redistributions}
          sub="AI-recommended transfers awaiting approval" icon={ArrowLeftRight} tone="info" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-white">District Health Index</h2>
            <Link to="/districts" className="text-xs text-accent-cyan hover:underline">View all →</Link>
          </div>
          <div className="space-y-2">
            {districts.slice(0, 6).map((d) => (
              <div key={d.district_id} className="flex items-center justify-between py-2 border-b border-base-700/40 last:border-0">
                <div>
                  <p className="text-sm font-medium text-white">{d.district_name}</p>
                  <p className="text-xs text-slate-500">{d.state_name} · {d.phc_count} PHCs</p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-32">
                    <div className="h-1.5 rounded-full bg-base-700 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${d.avg_stock_health_pct < 60 ? 'bg-accent-rose' : d.avg_stock_health_pct < 85 ? 'bg-accent-amber' : 'bg-accent-emerald'}`}
                        style={{ width: `${d.avg_stock_health_pct}%` }}
                      />
                    </div>
                  </div>
                  <StatusBadge status={d.status} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h2 className="font-semibold text-white mb-4">Critical Alerts</h2>
          <div className="space-y-3">
            {alerts.length === 0 && <p className="text-sm text-slate-500">No critical alerts right now.</p>}
            {alerts.map((a) => (
              <div key={a.id} className="p-3 rounded-xl bg-rose-500/5 border border-rose-500/20">
                <p className="text-xs font-semibold text-rose-400">{a.phc_name} · {a.district_name}</p>
                <p className="text-sm text-slate-300 mt-1">{a.message}</p>
              </div>
            ))}
          </div>
          <Link to="/alerts" className="text-xs text-accent-cyan hover:underline mt-4 inline-block">View all alerts →</Link>
        </div>
      </div>
    </div>
  )
}

export function LoadingState() {
  return <div className="text-slate-400 text-sm animate-pulse">Loading live data from Project API…</div>
}

export function ErrorState({ message }) {
  return (
    <div className="card border-rose-500/30">
      <p className="text-rose-400 font-medium">Couldn't reach the Project API.</p>
      <p className="text-slate-500 text-sm mt-1">
        Make sure the backend is running (<code className="text-slate-400">uvicorn app.main:app</code>) on port 8000. ({message})
      </p>
    </div>
  )
}
