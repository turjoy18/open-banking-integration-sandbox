import { useState } from 'react'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000'

function App() {
  const [customerId, setCustomerId] = useState('C001')
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function fetchAggregate(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setData(null)

    try {
      const response = await fetch(`${API_BASE}/aggregate/${encodeURIComponent(customerId)}`)
      const body = await response.json()

      if (!response.ok) {
        setError(body.detail || `Request failed (${response.status})`)
        return
      }

      setData(body)
    } catch (err) {
      setError('Could not reach API. Is the backend running on port 8000?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <header className="header">
        <h1>Open Banking Integration Sandbox</h1>
        <p>Lookup a customer aggregate from mock bank JSON + FX XML sources.</p>
      </header>

      <form className="panel" onSubmit={fetchAggregate}>
        <label htmlFor="customerId">Customer ID</label>
        <div className="row">
          <input
            id="customerId"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value.trim())}
            placeholder="C001"
          />
          <button type="submit" disabled={loading || !customerId}>
            {loading ? 'Loading…' : 'Fetch aggregate'}
          </button>
        </div>
      </form>

      {error && <div className="error">{error}</div>}

      {data && (
        <section className="panel results">
          <h2>Result for {data.customer_id}</h2>
          <p className="meta">Latency: {data.meta?.latency_ms} ms</p>

          <h3>Accounts</h3>
          <pre>{JSON.stringify(data.accounts, null, 2)}</pre>

          <h3>FX rates</h3>
          <pre>{JSON.stringify(data.fx_rates, null, 2)}</pre>
        </section>
      )}
    </div>
  )
}

export default App