import type { CannedExample } from '../types'

export function ExamplePicker({
  examples,
  onSelect,
}: {
  examples: CannedExample[]
  onSelect: (example: CannedExample) => void
}) {
  return (
    <div className="mt-4 flex flex-col gap-2">
      <span className="text-sm text-(--text)">Or try an example:</span>
      <div className="flex flex-wrap gap-2">
        {examples.map((example) => (
          <button
            className="cursor-pointer rounded-full border border-(--border) bg-transparent px-3.5 py-1.5 text-sm capitalize [font:inherit] text-(--text-h) hover:border-(--accent-border)"
            key={example.id}
            type="button"
            onClick={() => onSelect(example)}
          >
            {example.id.replace(/-/g, ' ')}
          </button>
        ))}
      </div>
    </div>
  )
}
