import { useCallback, useEffect, useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
const TOKEN_KEY = 'sandbox_access_token'
const CUSTOMER_KEY = 'sandbox_customer_id'
const CONSENT_KEY = 'sandbox_consent_id'
const STATE_KEY = 'sandbox_oauth_state'
const CLIENT_ID = import.meta.env.VITE_OAUTH_CLIENT_ID || 'sandbox-tpp'
const REDIRECT_URI =
  import.meta.env.VITE_OAUTH_REDIRECT_URI || `${window.location.origin}/callback`
const DEFAULT_SCOPES = 'accounts.read transactions.read payments.initiate'

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '')
  const [linkedCustomer, setLinkedCustomer] = useState(
    () => localStorage.getItem(CUSTOMER_KEY) || '',
  )
  const [authError, setAuthError] = useState('')
  const [authLoading, setAuthLoading] = useState(false)
  const [consents, setConsents] = useState([])

  const [customerId, setCustomerId] = useState(() => localStorage.getItem(CUSTOMER_KEY) || 'C001')
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState([])
  const [logsError, setLogsError] = useState('')
  const [logsLoading, setLogsLoading] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)

  const saveSession = (accessToken, customer, consentId) => {
    setToken(accessToken)
    setLinkedCustomer(customer || '')
    if (accessToken) {
      localStorage.setItem(TOKEN_KEY, accessToken)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
    if (customer) {
      localStorage.setItem(CUSTOMER_KEY, customer)
      setCustomerId(customer)
    } else {
      localStorage.removeItem(CUSTOMER_KEY)
    }
    if (consentId != null) {
      localStorage.setItem(CONSENT_KEY, String(consentId))
    } else {
      localStorage.removeItem(CONSENT_KEY)
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

  const fetchConsents = useCallback(async (accessToken) => {
    if (!accessToken) {
      setConsents([])
      return
    }
    try {
      const response = await fetch(`${API_BASE}/consents`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      if (!response.ok) {
        return
      }
      setConsents(await response.json())
    } catch {
      /* consent panel is best-effort */
    }
  }, [])

  /* eslint-disable react-hooks/set-state-in-effect -- mount/token fetches */
  useEffect(() => {
    void fetchLogs()
  }, [fetchLogs])

  useEffect(() => {
    void fetchConsents(token)
  }, [token, fetchConsents])
  /* eslint-enable react-hooks/set-state-in-effect */

  useEffect(() => {
    const path = window.location.pathname
    if (path !== '/callback') {
      return
    }
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    const state = params.get('state')
    const expected = sessionStorage.getItem(STATE_KEY)
    window.history.replaceState({}, '', '/')
    if (!code) {
      queueMicrotask(() => setAuthError('Authorization was cancelled or missing a code.'))
      return
    }
    if (!state || state !== expected) {
      queueMicrotask(() => setAuthError('OAuth state mismatch. Start Connect bank again.'))
      return
    }
    sessionStorage.removeItem(STATE_KEY)
    queueMicrotask(() => setAuthLoading(true))
    fetch(`${API_BASE}/tpp/oauth/exchange`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, state }),
    })
      .then(async (response) => {
        const body = await response.json()
        if (!response.ok) {
          setAuthError(body.detail || `Token exchange failed (${response.status})`)
          return
        }
        saveSession(body.access_token, body.customer_id, body.consent_id)
      })
      .catch(() => {
        setAuthError('Could not reach API to exchange the authorization code.')
      })
      .finally(() => setAuthLoading(false))
  }, [])

  function handleConnectBank() {
    const state = crypto.randomUUID()
    sessionStorage.setItem(STATE_KEY, state)
    const params = new URLSearchParams({
      response_type: 'code',
      client_id: CLIENT_ID,
      redirect_uri: REDIRECT_URI,
      scope: DEFAULT_SCOPES,
      state,
    })
    window.location.href = `${API_BASE}/oauth/authorize?${params.toString()}`
  }

  function handleLogout() {
    saveSession('', '', null)
    setData(null)
    setError('')
    setConsents([])
  }

  async function handleRevoke(consentId) {
    if (!token) {
      return
    }
    try {
      const response = await fetch(`${API_BASE}/consents/${consentId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) {
        setAuthError(`Could not revoke consent (${response.status})`)
        return
      }
      const current = localStorage.getItem(CONSENT_KEY)
      if (current && String(consentId) === current) {
        handleLogout()
        setAuthError('Consent revoked. Connect the bank again to continue.')
      } else {
        await fetchConsents(token)
      }
    } catch {
      setAuthError('Could not reach API to revoke consent.')
    }
  }

  async function fetchAggregate(event) {
    event.preventDefault()
    if (!token) {
      setError('Connect a bank first to fetch aggregates.')
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
          setError('Session expired or invalid. Please connect the bank again.')
          saveSession('', '', null)
        } else if (response.status === 403) {
          setError(body.detail || 'Consent missing, revoked, or does not cover this customer.')
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
        <p>TPP dashboard: customer consent, then aggregate mock bank JSON + FX XML.</p>
      </header>

      <section className="panel auth">
        <div className="logs-header">
          <h2>Bank connection</h2>
          {token ? (
            <button type="button" className="secondary" onClick={handleLogout}>
              Disconnect
            </button>
          ) : null}
        </div>

        {token ? (
          <p className="meta auth-status">
            Connected as {linkedCustomer || 'customer'}. Aggregate requests send a Bearer token bound
            to consent.
          </p>
        ) : (
          <div>
            <p className="meta hint">
              Redirects to the bank authorize page (demo / demo). Use http://127.0.0.1:5173 so the
              redirect URI matches.
            </p>
            <button type="button" onClick={handleConnectBank} disabled={authLoading}>
              {authLoading ? 'Connecting…' : 'Connect bank'}
            </button>
          </div>
        )}

        {authError && <div className="error">{authError}</div>}
      </section>

      {token && (
        <section className="panel">
          <h2>Consents</h2>
          {consents.length === 0 ? (
            <p className="meta">No consents returned for this customer.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Status</th>
                    <th>Scopes</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {consents.map((consent) => (
                    <tr key={consent.id}>
                      <td>{consent.id}</td>
                      <td>
                        <span className={consent.status === 'active' ? 'badge ok' : 'badge bad'}>
                          {consent.status}
                        </span>
                      </td>
                      <td>{consent.scopes}</td>
                      <td>
                        {consent.status === 'active' ? (
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => handleRevoke(consent.id)}
                          >
                            Revoke
                          </button>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

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
        {!token && <p className="meta hint">Connect a bank above to enable aggregate lookup.</p>}
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
