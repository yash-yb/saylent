import { NavLink } from 'react-router-dom'
import { LayoutDashboard, MapPinned, BellRing, ArrowLeftRight, Network, Activity } from 'lucide-react'

const links = [
  { to: '/', label: 'National Overview', icon: LayoutDashboard, end: true },
  { to: '/districts', label: 'Districts', icon: MapPinned },
  { to: '/alerts', label: 'Alerts', icon: BellRing },
  { to: '/redistribution', label: 'Redistribution', icon: ArrowLeftRight },
  { to: '/federated', label: 'Federated Learning', icon: Network },
  { to: '/phcs', label: 'PHC Explorer', icon: Activity },
]

export default function Sidebar() {
  return (
    <aside className="w-64 shrink-0 h-screen sticky top-0 bg-base-900 border-r border-base-700/60 flex flex-col">
      <div className="px-6 py-6 border-b border-base-700/60">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-indigo flex items-center justify-center font-extrabold text-base-950 text-sm">
            P
          </div>
          <span className="font-bold text-lg tracking-tight text-white">Saylent</span>
        </div>
        <p className="text-xs text-slate-400 mt-2 leading-relaxed">
          Federated AI for national health supply chain resilience
        </p>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-accent-indigo/15 text-accent-cyan border border-accent-indigo/30'
                  : 'text-slate-400 hover:text-white hover:bg-base-800'
              }`
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-4 py-4 border-t border-base-700/60 text-[11px] text-slate-500">
        BRICS Track 3 — Smart Health &amp;<br/>Supply Chain Resilience
      </div>
    </aside>
  )
}
