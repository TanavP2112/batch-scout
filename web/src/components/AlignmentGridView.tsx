import { FACET_NAMES, type AlignmentGrid } from '../types'
import { FACET_LABELS } from '../facetLabels'

export function AlignmentGridView({ grid }: { grid: AlignmentGrid }) {
  const cellClass = 'border-t border-(--border) px-1.5 py-1 text-left'

  return (
    <table className="w-full border-collapse text-[13px]">
      <tbody>
        {FACET_NAMES.map((facet) => {
          const cell = grid[facet]
          return (
            <tr key={facet}>
              <th className={`${cellClass} w-2/5 font-medium text-(--text)`} scope="row">
                {FACET_LABELS[facet]}
              </th>
              <td className={cellClass}>{cell.company_value}</td>
              <td className={`${cellClass} ${cell.same ? 'text-[#2a9d5c]' : 'text-(--text)'}`}>
                {cell.same ? '✓ same' : '✗ different'}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
