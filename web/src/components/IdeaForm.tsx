import { useState } from 'react'

export function IdeaForm({ onSubmit, disabled }: { onSubmit: (ideaText: string) => void; disabled: boolean }) {
  const [ideaText, setIdeaText] = useState('')

  return (
    <form
      className="idea-form"
      onSubmit={(e) => {
        e.preventDefault()
        if (ideaText.trim()) onSubmit(ideaText.trim())
      }}
    >
      <textarea
        value={ideaText}
        onChange={(e) => setIdeaText(e.target.value)}
        placeholder="Describe your startup idea..."
        rows={3}
      />
      <button type="submit" disabled={disabled || !ideaText.trim()}>
        {disabled ? 'Searching…' : 'Find prior art'}
      </button>
    </form>
  )
}
