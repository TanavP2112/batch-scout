import { useState } from 'react'

export function IdeaForm({ onSubmit, disabled }: { onSubmit: (ideaText: string) => void; disabled: boolean }) {
  const [ideaText, setIdeaText] = useState('')

  return (
    <form
      className="mt-6 flex flex-col gap-2"
      onSubmit={(e) => {
        e.preventDefault()
        if (ideaText.trim()) onSubmit(ideaText.trim())
      }}
    >
      <textarea
        className="resize-y rounded-lg border border-(--border) bg-(--bg) p-3 [font:inherit] text-(--text-h)"
        value={ideaText}
        onChange={(e) => setIdeaText(e.target.value)}
        placeholder="Describe your startup idea..."
        rows={3}
      />
      <button
        className="cursor-pointer self-start rounded-full bg-(--accent) px-5 py-2 [font:inherit] text-white disabled:cursor-default disabled:opacity-60"
        type="submit"
        disabled={disabled || !ideaText.trim()}
      >
        {disabled ? 'Searching…' : 'Find prior art'}
      </button>
    </form>
  )
}
