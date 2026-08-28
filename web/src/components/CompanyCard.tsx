import type { CompanyResult } from '../types'
import { AlignmentGridView } from './AlignmentGridView'

export function CompanyCard({ result }: { result: CompanyResult }) {
  const { company, alignment } = result
  return (
    <article className="company-card">
      <header>
        <h3>
          {company.website ? (
            <a href={company.website} target="_blank" rel="noreferrer">
              {company.name}
            </a>
          ) : (
            company.name
          )}
        </h3>
        <span className="meta">
          {company.batch} · {company.status}
        </span>
      </header>
      <p className="description">{company.one_liner}</p>
      <AlignmentGridView grid={alignment} />
    </article>
  )
}
