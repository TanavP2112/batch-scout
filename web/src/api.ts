import type { CannedExample, QueryResult } from './types'

export async function fetchExamples(): Promise<CannedExample[]> {
  const res = await fetch('/examples')
  if (!res.ok) throw new Error('failed to load examples')
  return res.json()
}

export class RateLimitedError extends Error {}

export async function submitQuery(ideaText: string): Promise<QueryResult> {
  const res = await fetch('/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ idea_text: ideaText }),
  })
  if (res.status === 429) {
    const body = await res.json().catch(() => null)
    throw new RateLimitedError(body?.detail ?? 'demo limit reached — please try again later')
  }
  if (!res.ok) throw new Error('query failed')
  return res.json()
}
