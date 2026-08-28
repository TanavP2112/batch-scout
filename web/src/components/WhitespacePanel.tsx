import { FACET_NAMES, type FacetName } from '../types'
import { FACET_LABELS } from '../facetLabels'

export function WhitespacePanel({ whitespace }: { whitespace: Record<FacetName, string[]> }) {
  const withGaps = FACET_NAMES.filter((facet) => whitespace[facet].length > 0)

  const heading = 'mb-2 text-lg leading-[1.18] font-medium tracking-[-0.24px] text-(--text-h)'

  if (withGaps.length === 0) {
    return (
      <section>
        <h2 className={heading}>Whitespace</h2>
        <p className="mb-2 text-sm text-(--text)">
          Every enum value in every facet is occupied by at least one of these companies.
        </p>
      </section>
    )
  }

  return (
    <section>
      <h2 className={heading}>Whitespace</h2>
      <p className="mb-2 text-sm text-(--text)">Enum values with zero occupants among the companies shown below.</p>
      {withGaps.map((facet) => (
        <div key={facet} className="flex items-baseline gap-3 py-1.5">
          <span className="w-27.5 shrink-0 text-[13px] text-(--text)">{FACET_LABELS[facet]}</span>
          <div className="flex max-h-27 flex-wrap gap-1.5 overflow-y-auto">
            {whitespace[facet].map((value) => (
              <span key={value} className="rounded-full bg-(--accent-bg) px-2.5 py-0.75 text-[13px] text-(--text-h)">
                {value}
              </span>
            ))}
          </div>
        </div>
      ))}
    </section>
  )
}
