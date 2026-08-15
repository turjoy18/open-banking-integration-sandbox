import { useCallback, useEffect, useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
const TOKEN_KEY = 'sandbox_access_token'

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '')
  const [username, setUsername] = useState('demo')
  const [password, setPassword] = useState('demo')
  const [authError, setAuthError] = useState('')
  const [authLoading, setAuthLoading] = useState(false)

  const [customerId, setCustomerId] = useState('C001')
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState([])
  const [logsError, setLogsError] = useState('')
  const [logsLoading, setLogsLoading] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)

  const saveToken = (value) => {
    setToken(value)
    if (value) {
      localStorage.setItem(TOKEN_KEY, value)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  const fetchLogs = useCallback(async () => {
    setLogsLoading(true)
    setLogsError('')
    try {
      const response = await fetch(`${API_BASE}/audit-logs?limit=10`)
      if (!response.ok) {
        setLogsError(`Failed to load logs (${response.status})`)
        return
      }
      const body = await response.json()
      setLogs(body)
      setLastUpdated(new Date())
    } catch {
      setLogsError('Could not load audit logs. Is the backend running?')
    } finally {
      setLogsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

  async function handleLogin(event) {
    event.preventDefault()
    setAuthLoading(true)
    setAuthError('')
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      const body = await response.json()
      if (!response.ok) {
        setAuthError(body.detail || `Login failed (${response.status})`)
        return
      }
      saveToken(body.access_token)
    } catch {
      setAuthError('Could not reach API. Is the backend running on port 8000?')
    } finally {
      setAuthLoading(false)
    }
  }

  function handleLogout() {
    saveToken('')
    setData(null)
    setError('')
  }

  async function fetchAggregate(event) {
    event.preventDefault()
    if (!token) {
      setError('Log in first to fetch aggregates.')
      return
    }

    setLoading(true)
    setError('')
    setData(null)

    try {
      const response = await fetch(`${API_BASE}/aggregate/${encodeURIComponent(customerId)}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const body = await response.json()

      if (!response.ok) {
        if (response.status === 401) {
          setError('Session expired or invalid. Please log in again.')
          saveToken('')
        } else {
          setError(body.detail || `Request failed (${response.status})`)
        }
        await fetchLogs()
        return
      }

      setData(body)
      await fetchLogs()
    } catch {
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

      <section className="panel auth">
        <div className="logs-header">
          <h2>Authentication</h2>
          {token ? (
            <button type="button" className="secondary" onClick={handleLogout}>
              Log out
            </button>
          ) : null}
        </div>

        {token ? (
          <p className="meta auth-status">Signed in. Aggregate requests will send a Bearer token.</p>
        ) : (
          <form onSubmit={handleLogin}>
            <div className="auth-grid">
              <div>
                <label htmlFor="username">Username</label>
                <input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                />
              </div>
              <div>
                <label htmlFor="password">Password</label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
              </div>
            </div>
            <p className="meta hint">Demo credentials: demo / demo</p>
            <button type="submit" disabled={authLoading || !username || !password}>
              {authLoading ? 'Signing in…' : 'Log in'}
            </button>
          </form>
        )}

        {authError && <div className="error">{authError}</div>}
      </section>

      <form className="panel" onSubmit={fetchAggregate}>
        <label htmlFor="customerId">Customer ID</label>
        <div className="row">
          <input
            id="customerId"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value.trim())}
            placeholder="C001"
          />
          <button type="submit" disabled={loading || !customerId || !token}>
            {loading ? 'Loading…' : 'Fetch aggregate'}
          </button>
        </div>
        {!token && <p className="meta hint">Log in above to enable aggregate lookup.</p>}
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

      <section className="panel logs">
        <div className="logs-header">
          <div>
            <h2>Recent audit logs</h2>
            <p className="meta">
              {lastUpdated
                ? `Last updated: ${lastUpdated.toLocaleTimeString()}`
                : 'Not loaded yet'}
            </p>
          </div>
          <button type="button" className="secondary" onClick={fetchLogs} disabled={logsLoading}>
            {logsLoading ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>

        {logsLoading && <p className="loading-status">Loading audit logs…</p>}

        {logsError && <div className="error">{logsError}</div>}

        {!logsError && logs.length === 0 && !logsLoading && (
          <p className="meta">No audit logs yet. Fetch an aggregate to create one.</p>
        )}

        {logs.length > 0 && (
          <div className={`table-wrap ${logsLoading ? 'is-loading' : ''}`}>
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Customer</th>
                  <th>Status</th>
                  <th>Latency</th>
                  <th>Endpoint</th>
                  <th>Summary</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td>{log.id}</td>
                    <td>{log.customer_id || '—'}</td>
                    <td>
                      <span className={log.status_code >= 400 ? 'badge bad' : 'badge ok'}>
                        {log.status_code}
                      </span>
                    </td>
                    <td>{log.latency_ms} ms</td>
                    <td>{log.endpoint}</td>
                    <td>{log.summary || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

export default App
