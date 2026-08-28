import { useEffect, useState } from 'react'
import { fetchExamples, submitQuery, RateLimitedError } from './api'
import type { CannedExample, QueryResult } from './types'
import { IdeaForm } from './components/IdeaForm'
import { ExamplePicker } from './components/ExamplePicker'
import { ResultsView } from './components/ResultsView'

export default function App() {
  const [examples, setExamples] = useState<CannedExample[]>([])
  const [ideaText, setIdeaText] = useState<string | null>(null)
  const [result, setResult] = useState<QueryResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchExamples()
      .then(setExamples)
      .catch(() => setExamples([]))
  }, [])

  function selectExample(example: CannedExample) {
    setIdeaText(example.idea_text)
    setResult(example.result)
    setError(null)
  }

  async function runQuery(text: string) {
    setIdeaText(text)
    setResult(null)
    setError(null)
    setLoading(true)
    try {
      setResult(await submitQuery(text))
    } catch (e) {
      setError(e instanceof RateLimitedError ? e.message : 'Something went wrong — try again or pick an example.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="px-6 pb-16 text-left">
      <header>
        <h1 className="mt-8 mb-2 text-4xl font-medium tracking-[-0.9px] text-(--text-h)">Prior-Art Engine</h1>
        <p className="max-w-[60ch] text-(--text)">
          Type a startup idea to see the closest YC companies, what's the same, what's different, and what's
          unoccupied.
        </p>
      </header>

      <IdeaForm onSubmit={runQuery} disabled={loading} />
      {examples.length > 0 && <ExamplePicker examples={examples} onSelect={selectExample} />}

      {error && <p className="mt-4 text-[#c0392b]">{error}</p>}
      {ideaText && !loading && <p className="mt-6 italic text-(--text)">“{ideaText}”</p>}
      {loading && <p className="mt-4 text-(--text)">Searching…</p>}
      {result && <ResultsView result={result} />}
    </div>
  )
}
