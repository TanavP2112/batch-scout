import type { CannedExample } from '../types'

export function ExamplePicker({
  examples,
  onSelect,
}: {
  examples: CannedExample[]
  onSelect: (example: CannedExample) => void
}) {
  return (
    <div className="example-picker">
      <span className="label">Or try an example:</span>
      <div className="example-list">
        {examples.map((example) => (
          <button key={example.id} type="button" onClick={() => onSelect(example)}>
            {example.id.replace(/-/g, ' ')}
          </button>
        ))}
      </div>
    </div>
  )
}
