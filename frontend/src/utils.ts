export type CardID = number
export type AttrKey = [string, string]
export type CompiledPattern = [Record<CardID, number>, Record<string, number>]
export type CardDatabase = Record<CardID, Record<string, string | undefined>>
export type CardAttrIndex = Record<CardID, Record<string, number>>

/**
 * Build a card attribute index: maps card ID to a count of its attributes.
 */
export function build_card_attribute_index(
    card_database: CardDatabase,
): CardAttrIndex {
    const index: CardAttrIndex = {}

    for (const card_id_str in card_database) {
        const card_id = Number(card_id_str)
        const info = card_database[card_id]
        const c: Record<string, number> = {}

        for (const [field, value] of Object.entries(info)) {
            if (value !== undefined && value !== null) {
                c[`${field},${value}`] = (c[`${field},${value}`] ?? 0) + 1
            }
        }

        index[card_id] = c
    }

    return index
}

/**
 * Compile ideal hand patterns into exact/wild format for fast matching.
 * Exact: {cardID: count}, Wild: {"field,value": count}
 */
export function compile_patterns(
    ideal_hands: (number | string)[][],
): CompiledPattern[] {
    const compiled: CompiledPattern[] = []

    for (const pattern of ideal_hands) {
        // Normalize: convert numeric-like strings to numbers, keep wildcards as-is
        const normalized = pattern.map((c) =>
            typeof c === 'string' && !c.startsWith('any_') ? Number(c) : c,
        )

        const counter: Record<number | string, number> = {}
        for (const c of normalized) {
            counter[c] = (counter[c] ?? 0) + 1
        }

        const exact: Record<CardID, number> = {}
        const wild: Record<string, number> = {}

        for (const [card, count] of Object.entries(counter)) {
            if (!isNaN(Number(card))) {
                exact[Number(card)] = count
            } else if (typeof card === 'string' && card.startsWith('any_')) {
                const parts = card.split('_', 3)
                if (parts.length !== 3)
                    throw new Error(`Invalid wildcard pattern: ${card}`)
                const [, field, value] = parts
                wild[`${field},${value}`] = count
            } else {
                throw new Error(
                    `Invalid pattern entry: ${card} (${typeof card})`,
                )
            }
        }

        compiled.push([exact, wild])
    }

    return compiled
}
