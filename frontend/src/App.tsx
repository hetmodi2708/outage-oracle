import { useState } from 'react'
import { searchIncidents } from './api'
import type { SearchResponse } from './types'
import { SearchBar } from './components/SearchBar'
import { LikelyCauses } from './components/LikelyCauses'
import { IncidentCard } from './components/IncidentCard'
import { EmptyState, ErrorState, IntroState, LoadingState } from './components/States'
import './App.css'

// One state at a time: nothing searched yet, waiting, failed, or showing a result
type Status =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | { kind: 'done'; result: SearchResponse }

function App() {
  const [query, setQuery] = useState('')
  const [lastQuery, setLastQuery] = useState('')
  const [status, setStatus] = useState<Status>({ kind: 'idle' })

  async function runSearch(q: string) {
    setLastQuery(q)
    setStatus({ kind: 'loading' })
    try {
      const result = await searchIncidents(q)
      setStatus({ kind: 'done', result })
    } catch (e) {
      setStatus({ kind: 'error', message: e instanceof Error ? e.message : 'Something went wrong.' })
    }
  }

  return (
    <div className="app">
      {/* Dark band: top bar + headline. The search card overlaps its bottom edge. */}
      <div className="masthead">
        <header className="topbar">
          <div className="brand">
            <span className="brand__mark" aria-hidden="true" />
            <span className="brand__name">Outage Oracle</span>
          </div>
          <a
            className="topbar__link"
            href="https://github.com/danluu/post-mortems"
            target="_blank"
            rel="noopener noreferrer"
          >
            Data source
          </a>
        </header>

        <section className="hero">
          <span className="hero__eyebrow">
            <span className="live-dot" aria-hidden="true" />
            196 public postmortems indexed
          </span>
          <h1>
            Search real outages <span className="hero__accent">by symptom</span>
          </h1>
          <p>
            Describe what's breaking. Get similar incidents from public engineering postmortems, with their root
            causes, fixes, and what to check first.
          </p>
        </section>
      </div>

      <main className="container">
        <SearchBar
          query={query}
          onQueryChange={setQuery}
          onSearch={runSearch}
          loading={status.kind === 'loading'}
        />

        <div className="results">
          {status.kind === 'idle' && <IntroState />}
          {status.kind === 'loading' && <LoadingState />}
          {status.kind === 'error' && <ErrorState message={status.message} onRetry={() => runSearch(lastQuery)} />}

          {status.kind === 'done' && status.result.incidents.length === 0 && <EmptyState />}

          {status.kind === 'done' && status.result.incidents.length > 0 && (
            <>
              <LikelyCauses markdown={status.result.likely_causes} confidence={status.result.confidence} />

              <section aria-labelledby="incidents-heading">
                <h2 id="incidents-heading" className="section-title">
                  Similar incidents <span className="section-title__count">{status.result.incidents.length}</span>
                </h2>
                <div className="cards">
                  {status.result.incidents.map((incident, i) => (
                    <IncidentCard key={incident.id} incident={incident} rank={i + 1} />
                  ))}
                </div>
              </section>
            </>
          )}
        </div>
      </main>

      <footer className="site-footer">
        <p>
          Built on public postmortems collected in{' '}
          <a href="https://github.com/danluu/post-mortems" target="_blank" rel="noopener noreferrer">
            danluu/post-mortems
          </a>
          . Summaries are LLM-generated and may be incomplete; always read the original postmortem.
        </p>
      </footer>
    </div>
  )
}

export default App
