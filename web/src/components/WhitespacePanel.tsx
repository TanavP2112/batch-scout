import { FACET_NAMES, type FacetName } from '../types'
import { FACET_LABELS } from '../facetLabels'

export function WhitespacePanel({ whitespace }: { whitespace: Record<FacetName, string[]> }) {
  const withGaps = FACET_NAMES.filter((facet) => whitespace[facet].length > 0)

  if (withGaps.length === 0) {
    return (
      <section className="whitespace-panel">
        <h2>Whitespace</h2>
        <p className="empty">Every enum value in every facet is occupied by at least one of these companies.</p>
      </section>
    )
  }

  return (
    <section className="whitespace-panel">
      <h2>Whitespace</h2>
      <p className="hint">Enum values with zero occupants among the companies shown below.</p>
      {withGaps.map((facet) => (
        <div key={facet} className="whitespace-row">
          <span className="facet-name">{FACET_LABELS[facet]}</span>
          <div className="chips">
            {whitespace[facet].map((value) => (
              <span key={value} className="chip">
                {value}
              </span>
            ))}
          </div>
        </div>
      ))}
    </section>
  )
}
