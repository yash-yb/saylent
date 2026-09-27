import { useEffect, useState } from 'react'
import { api } from '../api'
import StatusBadge from '../components/StatusBadge'
import { LoadingState, ErrorState } from './Dashboard'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function PHCExplorer() {
  const [phcs, setPhcs] = useState(null)
  const [error, setError] = useState(null)
  const [selectedPhc, setSelectedPhc] = useState(null)
  const [stock, setStock] = useState(null)
  const [forecast, setForecast] = useState(null)

  useEffect(() => {
    api.phcs().then((data) => {
      setPhcs(data)
      if (data.length) setSelectedPhc(data[0])
    }).catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!selectedPhc) return
    setForecast(null)
    api.phcStock(selectedPhc.id).then(setStock).catch((e) => setError(e.message))
  }, [selectedPhc])

  const loadForecast = (medicineId) => {
    api.phcForecast(selectedPhc.id, medicineId).then(setForecast).catch((e) => setError(e.message))
  }

  if (error) return <ErrorState message={error} />
  if (!phcs) return <LoadingState />

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-white">PHC Explorer</h1>
        <p className="text-sm text-slate-400 mt-1">Drill into any PHC's stock and 14-day demand forecast</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card">
          <h2 className="font-semibold text-white mb-3 text-sm">Select PHC</h2>
          <div className="space-y-1 max-h-[500px] overflow-y-auto pr-1">
            {phcs.map((p) => (
              <button key={p.id} onClick={() => setSelectedPhc(p)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
                  selectedPhc?.id === p.id ? 'bg-accent-indigo/20 text-accent-cyan' : 'text-slate-400 hover:bg-base-800'
                }`}>
                <p className="font-medium">{p.name}</p>
                <p className="text-xs opacity-70">{p.district_name}, {p.state_name}</p>
              </button>
            ))}
          </div>
        </div>

        <div className="card lg:col-span-2">
          <h2 className="font-semibold text-white mb-3 text-sm">
            Medicine Stock — {selectedPhc?.name}
          </h2>
          {!stock && <LoadingState />}
          {stock && (
            <div className="space-y-2">
              {stock.map((s) => (
                <button key={s.medicine_id} onClick={() => loadForecast(s.medicine_id)}
                  className="w-full flex items-center justify-between py-2 border-b border-base-700/40 last:border-0 text-left hover:bg-base-800/40 px-2 rounded-lg">
                  <div>
                    <p className="text-sm text-white">{s.medicine_name}</p>
                    <p className="text-xs text-slate-500">
                      {s.current_qty} {s.unit} on hand
                      {s.days_of_stock_left != null && ` · ${s.days_of_stock_left}d left`}
                    </p>
                  </div>
                  <StatusBadge status={s.status} />
                </button>
              ))}
            </div>
          )}

          {forecast && (
            <div className="mt-6 pt-6 border-t border-base-700/60">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-white">{forecast.medicine_name} — 14-day forecast</h3>
                {forecast.predicted_stockout_date && (
                  <span className="badge bg-rose-500/15 text-rose-400">
                    Stockout: {forecast.predicted_stockout_date}
                  </span>
                )}
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={forecast.forecast}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1c2740" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748b' }}
                    tickFormatter={(d) => d.slice(5)} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                  <Tooltip contentStyle={{ background: '#0f1526', border: '1px solid #1c2740', borderRadius: 8 }} />
                  <Line type="monotone" dataKey="predicted_demand" stroke="#22d3ee" strokeWidth={2} dot={false} name="Predicted demand" />
                </LineChart>
              </ResponsiveContainer>
              <p className="text-xs text-slate-500 mt-2">
                Method: {forecast.method}. Federated adjustment applied: {forecast.federated_adjustment_applied ? 'yes' : 'no'}.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
