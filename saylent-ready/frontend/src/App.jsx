import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Districts from './pages/Districts'
import Alerts from './pages/Alerts'
import Redistribution from './pages/Redistribution'
import Federated from './pages/Federated'
import PHCExplorer from './pages/PHCExplorer'

export default function App() {
  return (
    <div className="flex min-h-screen bg-base-950">
      <Sidebar />
      <main className="flex-1 px-8 py-8 max-w-[1400px]">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/districts" element={<Districts />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/redistribution" element={<Redistribution />} />
          <Route path="/federated" element={<Federated />} />
          <Route path="/phcs" element={<PHCExplorer />} />
        </Routes>
      </main>
    </div>
  )
}
