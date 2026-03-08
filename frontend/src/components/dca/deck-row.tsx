import { useState } from 'react'
import { useCardDatabase } from '../../hooks/useCardDatabase'
import type { Card, DeckLine } from '../../types/deck'

type DeckRowProps = {
    row: DeckLine
    index: number
    updateRow: (index: number, field: 'input' | 'count', value: string) => void
    selectSuggestion: (index: number, card: Card) => void
    removeRow: (index: number) => void
}

export function DeckRow({
    row,
    index,
    updateRow,
    selectSuggestion,
    removeRow,
}: DeckRowProps) {
    const { cards: cardDatabase } = useCardDatabase()
    const [suggestions, setSuggestions] = useState<Card[]>([])
    const [highlighted, setHighlighted] = useState(0)

    const handleInputChange = (value: string) => {
        updateRow(index, 'input', value)

        const matches = value
            ? cardDatabase
                  .filter((c) =>
                      c.name.toLowerCase().includes(value.toLowerCase()),
                  )
                  .slice(0, 5)
            : []

        setSuggestions(matches)
        setHighlighted(0)
    }

    const handleSuggestionClick = (card: Card) => {
        selectSuggestion(index, card)
        setSuggestions([])
        setHighlighted(0)
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (!suggestions.length) return

        let newIndex = highlighted

        if (e.key === 'ArrowDown') {
            newIndex = (highlighted + 1) % suggestions.length
            e.preventDefault()
        } else if (e.key === 'ArrowUp') {
            newIndex =
                (highlighted - 1 + suggestions.length) % suggestions.length
            e.preventDefault()
        } else if (e.key === 'Enter') {
            handleSuggestionClick(suggestions[highlighted])
            e.preventDefault()
            newIndex = 0
        }

        setHighlighted(newIndex)
    }

    return (
        <div className="relative flex gap-3 items-center bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
            <input
                type="number"
                min={1}
                max={3}
                value={row.count}
                onChange={(e) => updateRow(index, 'count', e.target.value)}
                className="w-16 border border-gray-200 rounded px-2 py-1"
            />

            <div className="flex-1 relative">
                <input
                    type="text"
                    value={row.input}
                    placeholder="Card name"
                    onChange={(e) => handleInputChange(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="w-full border border-gray-200 rounded px-3 py-1"
                />

                {suggestions.length > 0 && (
                    <ul className="absolute z-10 w-full bg-white border border-gray-300 rounded mt-1 max-h-40 overflow-y-auto shadow-md">
                        {suggestions.map((sugg, idx) => (
                            <li
                                key={sugg.id}
                                onClick={() => handleSuggestionClick(sugg)}
                                className={`px-3 py-1 cursor-pointer ${
                                    idx === highlighted
                                        ? 'bg-blue-200'
                                        : 'hover:bg-blue-100'
                                }`}
                            >
                                {sugg.name}
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            <button
                onClick={() => removeRow(index)}
                className="px-2 py-1 text-sm bg-red-400 text-white rounded"
            >
                Remove
            </button>
        </div>
    )
}
