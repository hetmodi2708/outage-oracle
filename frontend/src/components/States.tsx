// Small presentational components for the non-result states

export function LoadingState() {
  return (
    <div className="loading" role="status" aria-live="polite">
      <p className="loading__text">Searching postmortems and summarizing likely causes…</p>
      <div className="skeleton skeleton--panel" />
      {[1, 2, 3].map((i) => (
        <div key={i} className="skeleton skeleton--card" />
      ))}
    </div>
  )
}

export function EmptyState() {
  return (
    <div className="notice" role="status">
      <h2>No closely matching incidents</h2>
      <p>
        Try describing what you're observing rather than what you suspect: error messages, which metrics moved, what
        users saw, and what changed right before.
      </p>
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="notice notice--error" role="alert">
      <h2>Search failed</h2>
      <p>{message}</p>
      <button type="button" className="button button--secondary" onClick={onRetry}>
        Try again
      </button>
    </div>
  )
}

export function IntroState() {
  return (
    <div className="intro">
      <div className="intro__item">
        <span className="intro__step">1</span>
        <h3>Describe the symptom</h3>
        <p>Paste an error or describe what's breaking, the way you'd say it in an incident channel.</p>
      </div>
      <div className="intro__item">
        <span className="intro__step">2</span>
        <h3>Find similar outages</h3>
        <p>Your description is matched against the full text of real public postmortems.</p>
      </div>
      <div className="intro__item">
        <span className="intro__step">3</span>
        <h3>Learn from them</h3>
        <p>See each incident's root cause, how it was fixed, and a summary of likely causes for yours.</p>
      </div>
    </div>
  )
}
