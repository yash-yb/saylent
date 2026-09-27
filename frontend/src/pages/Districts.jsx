import { useEffect, useState } from 'react'
import { api } from '../api'
import StatusBadge from '../components/StatusBadge'
import { LoadingState, ErrorState } from './Dashboard'

export default function Districts() {
  const [districts, setDistricts] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.districtScores().then(setDistricts).catch((e) => setError(e.message))
  }, [])

  if (error) return <ErrorState message={error} />
  if (!districts) return <LoadingState />

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-white">Districts</h1>
        <p className="text-sm text-slate-400 mt-1">Ranked by stock health — most at-risk first</p>
      </header>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase text-slate-500 border-b border-base-700/60">
              <th className="px-5 py-3">District</th>
              <th className="px-5 py-3">State</th>
              <th className="px-5 py-3">PHCs</th>
              <th className="px-5 py-3">Stock Health</th>
              <th className="px-5 py-3">Bed Occupancy</th>
              <th className="px-5 py-3">Active Alerts</th>
              <th className="px-5 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {districts.map((d) => (
              <tr key={d.district_id} className="border-b border-base-700/30 last:border-0 hover:bg-base-800/50">
                <td className="px-5 py-3 font-medium text-white">{d.district_name}</td>
                <td className="px-5 py-3 text-slate-400">{d.state_name}</td>
                <td className="px-5 py-3 text-slate-400">{d.phc_count}</td>
                <td className="px-5 py-3 text-slate-300">{d.avg_stock_health_pct}%</td>
                <td className="px-5 py-3 text-slate-300">{d.bed_occupancy_pct}%</td>
                <td className="px-5 py-3 text-slate-300">{d.active_alerts}</td>
                <td className="px-5 py-3"><StatusBadge status={d.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
