import { useEffect, useState } from 'react'
import { api } from '../api'
import { LoadingState, ErrorState } from './Dashboard'
import { RefreshCw, Network } from 'lucide-react'

export default function Federated() {
  const [rounds, setRounds] = useState(null)
  const [error, setError] = useState(null)
  const [running, setRunning] = useState(false)

  const load = () => api.federatedRounds().then(setRounds).catch((e) => setError(e.message))
  useEffect(() => { load() }, [])

  const runCycle = async () => {
    setRunning(true)
    try {
      await api.runCycle()
      await load()
    } finally {
      setRunning(false)
    }
  }

  if (error) return <ErrorState message={error} />
  if (!rounds) return <LoadingState />

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Federated Learning</h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Every district trains a local demand-trend model on its own PHCs' consumption data.
            Only the model weights — never raw patient or stock records — travel to this
            aggregation step, which combines them via sample-weighted FedAvg into one national
            trend per medicine. This is what lets a low-history PHC's forecast benefit from
            national (and eventually cross-BRICS) patterns.
          </p>
        </div>
        <button onClick={runCycle} disabled={running}
          className="shrink-0 flex items-center gap-2 bg-accent-indigo/20 border border-accent-indigo/40 text-accent-cyan px-4 py-2 rounded-xl text-sm font-medium hover:bg-accent-indigo/30 disabled:opacity-50">
          <RefreshCw size={15} className={running ? 'animate-spin' : ''} />
          {running ? 'Running cycle…' : 'Run new FedAvg cycle'}
        </button>
      </header>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase text-slate-500 border-b border-base-700/60">
              <th className="px-5 py-3">Medicine</th>
              <th className="px-5 py-3">Round</th>
              <th className="px-5 py-3">Participating Districts</th>
              <th className="px-5 py-3">Global Trend (slope/day)</th>
              <th className="px-5 py-3">Global Baseline</th>
            </tr>
          </thead>
          <tbody>
            {rounds.map((r) => (
              <tr key={r.medicine_name} className="border-b border-base-700/30 last:border-0 hover:bg-base-800/50">
                <td className="px-5 py-3 font-medium text-white flex items-center gap-2">
                  <Network size={14} className="text-accent-indigo" /> {r.medicine_name}
                </td>
                <td className="px-5 py-3 text-slate-400">#{r.round_number}</td>
                <td className="px-5 py-3 text-slate-300">{r.participating_districts}</td>
                <td className="px-5 py-3 text-slate-300">{r.global_slope.toFixed(3)}</td>
                <td className="px-5 py-3 text-slate-300">{r.global_intercept.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
