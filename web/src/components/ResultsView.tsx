import type { QueryResult } from '../types'
import { CohortSignals } from './CohortSignals'
import { WhitespacePanel } from './WhitespacePanel'
import { CompanyCard } from './CompanyCard'

export function ResultsView({ result }: { result: QueryResult }) {
  return (
    <div className="mt-6 flex flex-col gap-6">
      <CohortSignals companies={result.companies.map((c) => c.company)} />
      <WhitespacePanel whitespace={result.whitespace} />
      <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4">
        {result.companies.map((c) => (
          <CompanyCard key={c.company.id} result={c} />
        ))}
      </div>
    </div>
  )
}
