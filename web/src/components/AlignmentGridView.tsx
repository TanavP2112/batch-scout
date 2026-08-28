import { FACET_NAMES, type AlignmentGrid } from '../types'
import { FACET_LABELS } from '../facetLabels'

export function AlignmentGridView({ grid }: { grid: AlignmentGrid }) {
  return (
    <table className="alignment-grid">
      <tbody>
        {FACET_NAMES.map((facet) => {
          const cell = grid[facet]
          return (
            <tr key={facet} className={cell.same ? 'same' : 'different'}>
              <th scope="row">{FACET_LABELS[facet]}</th>
              <td>{cell.company_value}</td>
              <td className="same-marker">{cell.same ? '✓ same' : '✗ different'}</td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
