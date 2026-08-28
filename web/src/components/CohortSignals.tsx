import type { Company } from '../types'

function countBy(companies: Company[], key: 'status' | 'stage'): Record<string, number> {
  const counts: Record<string, number> = {}
  for (const company of companies) {
    const value = String(company[key] ?? 'unknown')
    counts[value] = (counts[value] ?? 0) + 1
  }
  return counts
}

function median(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid]
}

export function CohortSignals({ companies }: { companies: Company[] }) {
  const statusCounts = countBy(companies, 'status')
  const batches = companies.map((c) => c.batch).filter(Boolean).sort()
  const teamSizes = companies.map((c) => c.team_size).filter((n) => typeof n === 'number' && n > 0)

  return (
    <section className="cohort-signals">
      <span>{companies.length} companies</span>
      {Object.entries(statusCounts).map(([status, count]) => (
        <span key={status}>
          {count} {status}
        </span>
      ))}
      {batches.length > 0 && (
        <span>
          batches {batches[0]}–{batches[batches.length - 1]}
        </span>
      )}
      {teamSizes.length > 0 && <span>median team size {median(teamSizes)}</span>}
    </section>
  )
}
