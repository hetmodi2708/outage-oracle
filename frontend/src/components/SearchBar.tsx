import type { FormEvent, KeyboardEvent } from 'react'

export const MAX_QUERY_LENGTH = 500 // matches the backend limit in backend/app.py

const EXAMPLES = [
  'Database connections maxed out right after a deploy',
  'Resolver returning SERVFAIL for valid domains',
  'CPU at 100% on every server after a firewall rule change',
  'Certificate expired, clients failing TLS handshake',
  'Queue consumers keep disconnecting, jobs piling up',
]

interface SearchBarProps {
  query: string
  onQueryChange: (query: string) => void
  onSearch: (query: string) => void
  loading: boolean
}

export function SearchBar({ query, onQueryChange, onSearch, loading }: SearchBarProps) {
  const tooLong = query.length > MAX_QUERY_LENGTH
  const canSubmit = query.trim().length > 0 && !tooLong && !loading

  function submit(e?: FormEvent) {
    e?.preventDefault()
    if (canSubmit) onSearch(query)
  }

  // Enter searches, Shift+Enter inserts a new line
  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  function runExample(example: string) {
    onQueryChange(example)
    onSearch(example)
  }

  return (
    <form className="search" onSubmit={submit}>
      <label htmlFor="query" className="search__label">
        What are you seeing?
      </label>
      <textarea
        id="query"
        className="search__input"
        rows={3}
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="e.g. 502s across all services after a config push, health checks timing out, can't reach internal dashboards"
        autoFocus
      />

      <div className="search__footer">
        <span className="search__hint">
          <kbd>Enter</kbd> to search · <kbd>Shift</kbd>+<kbd>Enter</kbd> for a new line
        </span>
        <span className={`search__count${tooLong ? ' is-over' : ''}`}>
          {query.length}/{MAX_QUERY_LENGTH}
        </span>
        <button type="submit" className="button button--icon" disabled={!canSubmit}>
          {loading ? (
            <span className="spinner" aria-hidden="true" />
          ) : (
            <svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true">
              <circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" strokeWidth="2" />
              <path d="M13 13l4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          )}
          {loading ? 'Searching…' : 'Search'}
        </button>
      </div>

      <div className="examples">
        <span className="examples__label">Try</span>
        {EXAMPLES.map((example) => (
          <button
            key={example}
            type="button"
            className="chip"
            onClick={() => runExample(example)}
            disabled={loading}
          >
            {example}
          </button>
        ))}
      </div>
    </form>
  )
}
