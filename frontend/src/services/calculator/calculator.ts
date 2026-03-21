export type CardID = number
export type AttrKey = [string, string]
export type ExactPattern = Record<CardID, number>
export type WildPattern = Record<string, number> // tuple key as string
export type CompiledPattern = [ExactPattern, WildPattern]
export type CardAttrIndex = Record<CardID, Record<string, number>>

export interface Card {
    superType: string
    name: string
    race?: string
    attribute?: string
}

export type CardDatabase = Record<CardID, Card>
export type DiscardConstraint = [string, string]

export interface GambleCard {
    draw: number
    discard?: DiscardConstraint[]
}

export type GamblingCards = Record<CardID, GambleCard>

export interface HandTestResult {
    matches_without_gambling: number
    matches_with_gambling: number
    rescued_with_gambling: number
    useful_gambles: Map<CardID, number>
    gamble_seen: Map<CardID, number>
    gamble_attempted: number
    gamble_failed: number
    gamble_unplayable: number
}

export interface ConsistencyResult {
    num_hands: number
    p5: number
    p6: number
    p5_with_gambling: number
    p6_with_gambling: number
    rescued_5: number
    rescued_6: number
    useful_gambles_5: Map<CardID, number>
    useful_gambles_6: Map<CardID, number>
    gamble_seen_5: Map<CardID, number>
    gamble_seen_6: Map<CardID, number>
    gamble_attempted_5: number
    gamble_attempted_6: number
    failed_gambles_5: number
    failed_gambles_6: number
    unplayable_gambles_5: number
    unplayable_gambles_6: number
    near_miss_counts: Map<CardID, number>
    blocking_card_counts: Map<CardID, number>
    ideal_hand_counts: Map<CardID, number>
    matched_pattern_counts_5: Map<number, number>
    matched_pattern_counts_6: Map<number, number>
    matched_pattern_counts_5_withgamble: Map<number, number>
    matched_pattern_counts_6_withgamble: Map<number, number>
}

function counter<T>(iterable: T[]): Map<T, number> {
    const map = new Map<T, number>()
    for (const item of iterable) {
        map.set(item, (map.get(item) || 0) + 1)
    }
    return map
}

function randomIndex(max: number): number {
    return Math.floor(Math.random() * max)
}

export function hand_is_good(
    hand: CardID[],
    ideal_hands: (CardID[] | Map<CardID, number>)[],
): boolean {
    const hand_counter = counter(hand)

    const ideal_counters = ideal_hands.map((pattern) =>
        pattern instanceof Map ? pattern : counter(pattern as CardID[]),
    )

    return ideal_counters.some((pattern) =>
        Array.from(pattern.entries()).every(
            ([card, count]) => (hand_counter.get(card) || 0) >= count,
        ),
    )
}

export function hand_is_wild(
    hand: CardID[],
    compiled_patterns: CompiledPattern[],
    card_attr_index: CardAttrIndex,
): number {
    const hand_counter: Record<CardID, number> = {}
    const attr_counter: Record<string, number> = {}

    for (const c of hand) {
        hand_counter[c] = (hand_counter[c] || 0) + 1
    }

    for (const card of hand) {
        const attrs = card_attr_index[card]
        if (attrs) {
            for (const [attr, val] of Object.entries(attrs)) {
                attr_counter[attr] = (attr_counter[attr] || 0) + val
            }
        }
    }

    let matched_count = 0

    for (const [exact, wild] of compiled_patterns) {
        const remaining_attrs: Record<string, number> = {}

        let exact_match = true
        for (const [cardStr, count] of Object.entries(exact)) {
            const card = Number(cardStr)
            if ((hand_counter[card] || 0) < count) {
                exact_match = false
                break
            }
            const attrs = card_attr_index[card]
            if (attrs) {
                for (const [attr, val] of Object.entries(attrs)) {
                    remaining_attrs[attr] =
                        (remaining_attrs[attr] || 0) - val * count
                }
            }
        }
        if (!exact_match) continue

        let wild_match = true
        for (const [attr, count] of Object.entries(wild)) {
            if (
                (attr_counter[attr] || 0) + (remaining_attrs[attr] || 0) <
                count
            ) {
                wild_match = false
                break
            }
        }

        if (wild_match) matched_count += 1
    }

    return matched_count
}

export function run_test_hand_without_gambling(
    hand_checker: (hand: CardID[]) => number,
    hand: CardID[],
): HandTestResult {
    const result = hand_checker(hand)
    return {
        matches_without_gambling: result,
        matches_with_gambling: result,
        rescued_with_gambling: 0,
        useful_gambles: new Map(),
        gamble_seen: new Map(),
        gamble_attempted: 0,
        gamble_failed: 0,
        gamble_unplayable: 0,
    }
}

export function run_test_hand_with_gambling(
    hand_checker: (hand: CardID[]) => number,
    hand: CardID[],
    card_attr_index: CardAttrIndex,
    remaining_deck: CardID[],
    gambling_cards: GamblingCards,
): HandTestResult {
    let matches_without = hand_checker(hand)
    let matches_with = matches_without
    let rescued_with_gambling = 0

    const useful_gambles = new Map<CardID, number>()
    const gamble_seen = new Map<CardID, number>()
    let gamble_attempted = 0
    let gamble_failed = 0
    let gamble_unplayable = 0

    if (matches_without > 0) {
        return {
            matches_without_gambling: matches_without,
            matches_with_gambling: matches_with,
            rescued_with_gambling,
            useful_gambles,
            gamble_seen,
            gamble_attempted,
            gamble_failed,
            gamble_unplayable,
        }
    }

    const gamble_card = hand.find((c) => gambling_cards[c] !== undefined)
    if (gamble_card === undefined) {
        return {
            matches_without_gambling: matches_without,
            matches_with_gambling: matches_with,
            rescued_with_gambling,
            useful_gambles,
            gamble_seen,
            gamble_attempted,
            gamble_failed,
            gamble_unplayable,
        }
    }

    gamble_seen.set(gamble_card, (gamble_seen.get(gamble_card) || 0) + 1)

    const spec = gambling_cards[gamble_card]
    const discard_requirements = spec.discard ?? []

    let discardable: CardID[] = []

    if (discard_requirements.length > 0) {
        discardable = hand.filter((c) =>
            discard_requirements.some(
                ([field, value]) =>
                    card_attr_index[c]?.[`${field},${value}`] > 0,
            ),
        )
        if (discardable.length === 0) {
            gamble_unplayable += 1
            return {
                matches_without_gambling: matches_without,
                matches_with_gambling: matches_with,
                rescued_with_gambling,
                useful_gambles,
                gamble_seen,
                gamble_attempted,
                gamble_failed,
                gamble_unplayable,
            }
        }
    }

    const new_hand = hand.slice()
    new_hand.splice(new_hand.indexOf(gamble_card), 1)

    const num_to_draw = spec.draw ?? 0
    if (remaining_deck.length < num_to_draw) {
        gamble_unplayable += 1
        return {
            matches_without_gambling: matches_without,
            matches_with_gambling: matches_with,
            rescued_with_gambling,
            useful_gambles,
            gamble_seen,
            gamble_attempted,
            gamble_failed,
            gamble_unplayable,
        }
    }

    gamble_attempted += 1

    // Draw random cards without replacement
    const drawn_cards: CardID[] = []
    const temp_deck = remaining_deck.slice()
    for (let i = 0; i < num_to_draw; i++) {
        const idx = randomIndex(temp_deck.length)
        drawn_cards.push(temp_deck[idx])
        temp_deck.splice(idx, 1)
    }

    new_hand.push(...drawn_cards)

    // Remove discardable cards
    for (const c of new_hand) {
        if (
            discard_requirements.some(
                ([field, value]) =>
                    card_attr_index[c]?.[`${field},${value}`] > 0,
            )
        ) {
            new_hand.splice(new_hand.indexOf(c), 1)
            break
        }
    }

    if (hand_checker(new_hand) > 0) {
        matches_with = 1
        rescued_with_gambling = 1
        useful_gambles.set(
            gamble_card,
            (useful_gambles.get(gamble_card) || 0) + 1,
        )
    } else {
        gamble_failed += 1
    }

    return {
        matches_without_gambling: matches_without,
        matches_with_gambling: matches_with,
        rescued_with_gambling,
        useful_gambles,
        gamble_seen,
        gamble_attempted,
        gamble_failed,
        gamble_unplayable,
    }
}

export function simple_consistency(
    deckcount: number,
    ratios: number[],
    names: number[],
    hand_tester: (deck: CardID[], hand: CardID[]) => HandTestResult,
    num_hands = 1_000_000,
): ConsistencyResult {
    ratios = [...ratios]
    names = [...names]

    const blanks = deckcount - ratios.reduce((a, b) => a + b, 0)
    if (blanks < 0) throw new Error('Ratios add up to more than deck count')
    if (blanks > 0) {
        ratios.push(blanks)
        names.push(0)
    }

    const deck: CardID[] = []
    for (let i = 0; i < names.length; i++) {
        for (let j = 0; j < ratios[i]; j++) {
            deck.push(names[i])
        }
    }

    deckcount = deck.length

    let good_5 = 0,
        good_6 = 0,
        rescued_5 = 0,
        rescued_6 = 0,
        failed_gambles_5 = 0,
        failed_gambles_6 = 0,
        unplayable_gambles_5 = 0,
        unplayable_gambles_6 = 0,
        gamble_attempted_5 = 0,
        gamble_attempted_6 = 0

    const gamble_seen_5 = new Map<CardID, number>()
    const gamble_seen_6 = new Map<CardID, number>()
    const useful_gambles_5 = new Map<CardID, number>()
    const useful_gambles_6 = new Map<CardID, number>()

    const near_miss_counts = new Map<CardID, number>()
    const blocking_card_counts = new Map<CardID, number>()
    const ideal_hand_counts = new Map<CardID, number>()
    const matched_pattern_counts_5 = new Map<number, number>()
    const matched_pattern_counts_6 = new Map<number, number>()
    const matched_pattern_counts_5_withgamble = new Map<number, number>()
    const matched_pattern_counts_6_withgamble = new Map<number, number>()

    for (let n = 0; n < num_hands; n++) {
        const hand5: CardID[] = []
        const temp_deck = deck.slice()
        for (let i = 0; i < Math.min(5, deckcount); i++) {
            const idx = randomIndex(temp_deck.length)
            hand5.push(temp_deck[idx])
            temp_deck.splice(idx, 1)
        }

        const result5 = hand_tester(temp_deck, hand5.slice())

        matched_pattern_counts_5.set(
            result5.matches_without_gambling,
            (matched_pattern_counts_5.get(result5.matches_without_gambling) ||
                0) + 1,
        )

        const total_matches_5 =
            result5.matches_without_gambling + result5.rescued_with_gambling
        matched_pattern_counts_5_withgamble.set(
            total_matches_5,
            (matched_pattern_counts_5_withgamble.get(total_matches_5) || 0) + 1,
        )

        if (result5.matches_without_gambling > 0) {
            good_5 += 1
            for (const c of hand5)
                ideal_hand_counts.set(c, (ideal_hand_counts.get(c) || 0) + 1)
        } else {
            for (const c of hand5)
                blocking_card_counts.set(
                    c,
                    (blocking_card_counts.get(c) || 0) + 1,
                )
            for (const c of deck.filter((d) => !hand5.includes(d))) {
                near_miss_counts.set(c, (near_miss_counts.get(c) || 0) + 1)
            }
        }

        rescued_5 += result5.rescued_with_gambling
        failed_gambles_5 += result5.gamble_failed
        unplayable_gambles_5 += result5.gamble_unplayable
        gamble_attempted_5 += result5.gamble_attempted

        result5.gamble_seen.forEach((v, k) =>
            gamble_seen_5.set(k, (gamble_seen_5.get(k) || 0) + v),
        )
        result5.useful_gambles.forEach((v, k) =>
            useful_gambles_5.set(k, (useful_gambles_5.get(k) || 0) + v),
        )

        if (deckcount >= 6) {
            const temp_deck_for_6 = temp_deck.slice()
            const extra_card = temp_deck_for_6[randomIndex(temp_deck.length)]
            const hand6 = hand5.concat(extra_card)
            temp_deck_for_6.splice(temp_deck_for_6.indexOf(extra_card), 1)

            const result6 = hand_tester(temp_deck_for_6, hand6)

            matched_pattern_counts_6.set(
                result6.matches_without_gambling,
                (matched_pattern_counts_6.get(
                    result6.matches_without_gambling,
                ) || 0) + 1,
            )

            const total_matches_6 =
                result6.matches_without_gambling + result6.rescued_with_gambling
            matched_pattern_counts_6_withgamble.set(
                total_matches_6,
                (matched_pattern_counts_6_withgamble.get(total_matches_6) ||
                    0) + 1,
            )

            if (result6.matches_without_gambling > 0) {
                good_6 += 1
                for (const c of hand6)
                    ideal_hand_counts.set(
                        c,
                        (ideal_hand_counts.get(c) || 0) + 1,
                    )
            } else {
                for (const c of hand6)
                    blocking_card_counts.set(
                        c,
                        (blocking_card_counts.get(c) || 0) + 1,
                    )
                for (const c of deck.filter((d) => !hand6.includes(d))) {
                    near_miss_counts.set(c, (near_miss_counts.get(c) || 0) + 1)
                }
            }

            rescued_6 += result6.rescued_with_gambling
            failed_gambles_6 += result6.gamble_failed
            unplayable_gambles_6 += result6.gamble_unplayable
            gamble_attempted_6 += result6.gamble_attempted

            result6.gamble_seen.forEach((v, k) =>
                gamble_seen_6.set(k, (gamble_seen_6.get(k) || 0) + v),
            )
            result6.useful_gambles.forEach((v, k) =>
                useful_gambles_6.set(k, (useful_gambles_6.get(k) || 0) + v),
            )
        }
    }

    const p5 = good_5 / num_hands
    const p6 = deckcount >= 6 ? good_6 / num_hands : 0.0
    const p5_with_gambling = (good_5 + rescued_5) / num_hands
    const p6_with_gambling =
        deckcount >= 6 ? (good_6 + rescued_6) / num_hands : 0.0

    return {
        num_hands,
        p5,
        p6,
        p5_with_gambling,
        p6_with_gambling,
        rescued_5,
        rescued_6,
        useful_gambles_5,
        useful_gambles_6,
        gamble_seen_5,
        gamble_seen_6,
        gamble_attempted_5,
        gamble_attempted_6,
        failed_gambles_5,
        failed_gambles_6,
        unplayable_gambles_5,
        unplayable_gambles_6,
        near_miss_counts,
        blocking_card_counts,
        ideal_hand_counts,
        matched_pattern_counts_5,
        matched_pattern_counts_6,
        matched_pattern_counts_5_withgamble,
        matched_pattern_counts_6_withgamble,
    }
}
