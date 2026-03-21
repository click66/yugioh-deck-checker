export type Card = {
    id: number
    name: string
}

export type Wildcard = { id: string; name: string; wildcard: true }

export type DeckLine = {
    card: Card | Wildcard | null
    input: string
    count: number | ''
}

export type HandItem = Card | Wildcard
