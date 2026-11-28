import type { SearchResponse } from './types'

// In dev, Vite proxies /api to http://localhost:8000 (see vite.config.ts).
// For deployment, set VITE_API_URL to the backend's public URL at build time.
const API_URL = import.meta.env.VITE_API_URL ?? '/api'

const UNREACHABLE = "Can't reach the Outage Oracle server. Make sure the backend is running (uv run uvicorn backend.app:app --reload)."

export async function searchIncidents(query: string): Promise<SearchResponse> {
  let res: Response
  try {
    res = await fetch(`${API_URL}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    })
  } catch {
    // fetch() only throws when there is no HTTP response at all (server down, network error)
    throw new Error(UNREACHABLE)
  }

  // Vite's dev proxy answers 500/502/504 itself when FastAPI isn't running
  if ([500, 502, 503, 504].includes(res.status) && !res.headers.get('content-type')?.includes('json')) {
    throw new Error(UNREACHABLE)
  }

  if (!res.ok) {
    // FastAPI's HTTPException sends {"detail": "..."} - surface that message to the user
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed (${res.status})`)
  }

  return res.json()
}
