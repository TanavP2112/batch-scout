import { useEffect, useState } from 'react'
import { fetchExamples, submitQuery, RateLimitedError } from './api'
import type { CannedExample, QueryResult } from './types'
import { IdeaForm } from './components/IdeaForm'
import { ExamplePicker } from './components/ExamplePicker'
import { ResultsView } from './components/ResultsView'
import './App.css'

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
    <div className="app">
      <header className="app-header">
        <h1>Prior-Art Engine</h1>
        <p>Type a startup idea to see the closest YC companies, what's the same, what's different, and what's unoccupied.</p>
      </header>

      <IdeaForm onSubmit={runQuery} disabled={loading} />
      {examples.length > 0 && <ExamplePicker examples={examples} onSelect={selectExample} />}

      {error && <p className="error">{error}</p>}
      {ideaText && !loading && <p className="idea-echo">“{ideaText}”</p>}
      {loading && <p className="loading">Searching…</p>}
      {result && <ResultsView result={result} />}
    </div>
  )
}
