const BASE = '/api'

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`)
  return res.json()
}

async function post(path) {
  const res = await fetch(`${BASE}${path}`, { method: 'POST' })
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`)
  return res.json()
}

export const api = {
  nationalSummary: () => get('/national/summary'),
  districtScores: () => get('/national/districts'),
  phcs: () => get('/phc'),
  phcStock: (id) => get(`/phc/${id}/stock`),
  phcForecast: (id, medId) => get(`/phc/${id}/forecast/${medId}`),
  alerts: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return get(`/alerts${qs ? `?${qs}` : ''}`)
  },
  resolveAlert: (id) => post(`/alerts/${id}/resolve`),
  redistribution: (status = 'pending') => get(`/redistribution?status=${status}`),
  approveRedistribution: (id) => post(`/redistribution/${id}/approve`),
  rejectRedistribution: (id) => post(`/redistribution/${id}/reject`),
  federatedRounds: () => get('/federated/rounds'),
  runCycle: () => post('/federated/run-cycle'),
}
