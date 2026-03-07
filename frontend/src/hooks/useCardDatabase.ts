import { useState, useEffect } from 'react'
import { z } from 'zod'

const CardSchema = z.object({
    id: z.number(),
    name: z.string(),
})

const CardArraySchema = z.array(CardSchema)

type Card = z.infer<typeof CardSchema>
type Manifest = { file: string }

export function useCardDatabase() {
    const [cards, setCards] = useState<Card[]>([])
    const [loading, setLoading] = useState<boolean>(true)

    useEffect(() => {
        fetch('/database-latest.json', { cache: 'no-store' })
            .then((resp) => {
                return resp.ok ? (resp.json() as Promise<Manifest>) : null
            })
            .then((manifest) =>
                manifest
                    ? fetch(`/data/${manifest.file}`, {
                          cache: 'no-store',
                      }).then((resp) => {
                          return resp.ok ? resp.json() : []
                      })
                    : [],
            )
            .then((rawData) => {
                const parsed = Array.isArray(rawData)
                    ? CardArraySchema.safeParse(rawData)
                    : null
                setCards(parsed?.success ? parsed.data : [])
            })
            .catch(() => setCards([]))
            .finally(() => setLoading(false))
    }, [])

    return { cards, loading }
}
