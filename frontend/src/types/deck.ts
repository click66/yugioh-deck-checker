export type Card = {
    id: number
    name: string
}

export type DeckLine = {
    card: Card | null
    input: string
    count: number | ''
}
