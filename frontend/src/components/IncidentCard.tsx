import type { Incident } from '../types'

interface IncidentCardProps {
  incident: Incident
  rank: number
}

// "config-change" -> "Config change"
function humanize(value: string) {
  const text = value.replace(/-/g, ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

// Categories that have a color in App.css; anything unexpected falls back to "other"
const KNOWN_CATEGORIES = ['database', 'network', 'dns', 'compute', 'storage', 'auth-cert', 'application']

function categoryClass(category: string) {
  return KNOWN_CATEGORIES.includes(category) ? `cat-${category}` : 'cat-other'
}

// Signal-strength bars for similarity. Chunk similarities in this app mostly fall between ~0.42
// (the backend's cutoff) and ~0.75, so we spread that range across 4 bars.
function SignalBars({ value }: { value: number }) {
  const filled = Math.max(1, Math.min(4, Math.ceil(((value - 0.42) / (0.75 - 0.42)) * 4)))
  return (
    <span className="signal" title={`Similarity of the best-matching passage: ${value.toFixed(2)}`}>
      <span className="signal__bars" aria-hidden="true">
        {[1, 2, 3, 4].map((bar) => (
          <span key={bar} className={bar <= filled ? 'is-on' : ''} />
        ))}
      </span>
      <span className="signal__value">{value.toFixed(2)}</span>
    </span>
  )
}

export function IncidentCard({ incident, rank }: IncidentCardProps) {
  return (
    <article className={`card ${categoryClass(incident.category)}`} id={`incident-${rank}`}>
      <header className="card__header">
        <span className="card__rank" aria-label={`Result ${rank}`}>
          {rank}
        </span>
        <div className="card__title">
          <h3>{incident.company}</h3>
          <div className="tags">
            <span className="tag tag--category">{humanize(incident.category)}</span>
            <span className="tag tag--outline">Trigger: {humanize(incident.trigger)}</span>
          </div>
        </div>
        <SignalBars value={incident.similarity} />
      </header>

      <dl className="card__fields">
        <div className="field field--cause">
          <dt>Root cause</dt>
          <dd>{incident.root_cause}</dd>
        </div>
        <div className="field field--fix">
          <dt>How it was fixed</dt>
          <dd>{incident.fix}</dd>
        </div>
        <div className="field field--prevention">
          <dt>Prevention</dt>
          <dd>{incident.prevention}</dd>
        </div>
      </dl>

      <footer className="card__footer">
        <details className="matched">
          <summary>Why this matched</summary>
          <blockquote>{incident.matched_text}</blockquote>
        </details>
        <a className="card__link" href={incident.url} target="_blank" rel="noopener noreferrer">
          Read the full postmortem →
        </a>
      </footer>
    </article>
  )
}
