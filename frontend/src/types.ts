// These mirror the dict returned by retrieval/generate.py -> generate().
// If you change the backend response, change these too.

export interface Incident {
  id: string
  company: string
  url: string
  category: string
  trigger: string
  root_cause: string
  fix: string
  prevention: string
  similarity: number
  matched_text: string
}

export interface SearchResponse {
  query: string
  likely_causes: string // markdown from the LLM, or "No match found"
  confidence: number
  incidents: Incident[] // empty when nothing matched closely enough
}
