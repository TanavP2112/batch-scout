import type { QueryResult } from '../types'
import { CohortSignals } from './CohortSignals'
import { WhitespacePanel } from './WhitespacePanel'
import { CompanyCard } from './CompanyCard'

export function ResultsView({ result }: { result: QueryResult }) {
  return (
    <div className="results-view">
      <CohortSignals companies={result.companies.map((c) => c.company)} />
      <WhitespacePanel whitespace={result.whitespace} />
      <div className="company-grid">
        {result.companies.map((c) => (
          <CompanyCard key={c.company.id} result={c} />
        ))}
      </div>
    </div>
  )
}
