import { hand_is_wild } from '../../../src/services/calculator/calculator'
import { build_card_attribute_index, compile_patterns } from '../../../src/utils'

// Minimal mock card database keyed by card ID
const CARD_DATABASE = {
    80181649: { superType: 'spell', name: 'A Case for K9' },
    86988864: { superType: 'monster', race: 'Beast', name: '3-Hump Lacooda' },
    14261867: {
        superType: 'monster',
        attribute: 'DARK',
        race: 'Insect',
        name: '8-Claws Scorpion',
    },
    23771716: {
        superType: 'normal',
        attribute: 'WATER',
        race: 'Fish',
        name: '7 Colored Fish',
    },
    6850209: {
        superType: 'spell',
        attribute: 'DARK',
        race: 'Quick-Play',
        name: 'A Deal with Dark Ruler',
    },
    68170903: { superType: 'trap', name: 'A Feint Plan' },
}

const CARD_ATTRIBUTE_INDEX = build_card_attribute_index(CARD_DATABASE)

describe('hand_is_wild', () => {
    test('exact match', () => {
        const hand = [80181649, 86988864]
        const ideal_hands = [[80181649, 86988864]]
        expect(
            hand_is_wild(
                hand,
                compile_patterns(ideal_hands),
                CARD_ATTRIBUTE_INDEX,
            ),
        ).toBe(1)
    })

    test('no match', () => {
        const hand = [80181649, 86988864]
        const ideal_hands = [[80181649, 14261867]]
        expect(
            hand_is_wild(
                hand,
                compile_patterns(ideal_hands),
                CARD_ATTRIBUTE_INDEX,
            ),
        ).toBe(0)
    })

    test('wildcard string any_superType_spell', () => {
        const hand = [80181649, 86988864]
        const ideal_hands = [[86988864, 'any_superType_spell']]
        expect(
            hand_is_wild(
                hand,
                compile_patterns(ideal_hands),
                CARD_ATTRIBUTE_INDEX,
            ),
        ).toBe(1)

        const hand2 = [86988864, 68170903]
        expect(
            hand_is_wild(
                hand2,
                compile_patterns(ideal_hands),
                CARD_ATTRIBUTE_INDEX,
            ),
        ).toBe(0)
    })

    test('wildcard does not consider specifics', () => {
        const hand = [80181649, 86988864]
        const ideal_hands = [[80181649, 'any_superType_spell']]
        expect(
            hand_is_wild(
                hand,
                compile_patterns(ideal_hands),
                CARD_ATTRIBUTE_INDEX,
            ),
        ).toBe(0)
    })

    test('wildcard considers duplicates', () => {
        const hand = [80181649, 80181649, 86988864]
        const ideal_hands = [[80181649, 'any_superType_spell']]
        expect(
            hand_is_wild(
                hand,
                compile_patterns(ideal_hands),
                CARD_ATTRIBUTE_INDEX,
            ),
        ).toBe(1)
    })

    test('multiple wildcards', () => {
        const hand = [80181649, 80181649, 6850209]
        const ideal_hands = [
            [80181649, 'any_superType_spell', 'any_superType_spell'],
        ]
        expect(
            hand_is_wild(
                hand,
                compile_patterns(ideal_hands),
                CARD_ATTRIBUTE_INDEX,
            ),
        ).toBe(1)
    })

    test('multiple wildcards larger hand', () => {
        const hand = [80181649, 6850209]
        const ideal_hands = [
            [80181649, 'any_superType_spell', 'any_superType_spell'],
        ]
        expect(
            hand_is_wild(
                hand,
                compile_patterns(ideal_hands),
                CARD_ATTRIBUTE_INDEX,
            ),
        ).toBe(0)
    })

    test('multiple wildcards larger hand duplicates', () => {
        const hand = [80181649, 80181649]
        const ideal_hands = [
            [80181649, 'any_superType_spell', 'any_superType_spell'],
        ]
        expect(
            hand_is_wild(
                hand,
                compile_patterns(ideal_hands),
                CARD_ATTRIBUTE_INDEX,
            ),
        ).toBe(0)
    })

    test('duplicates in hand', () => {
        const hand = [80181649, 80181649, 86988864]
        const ideal_hands = [[80181649, 80181649]]
        expect(
            hand_is_wild(
                hand,
                compile_patterns(ideal_hands),
                CARD_ATTRIBUTE_INDEX,
            ),
        ).toBe(1)

        const ideal_hands2 = [[80181649, 80181649, 80181649]]
        expect(
            hand_is_wild(
                hand,
                compile_patterns(ideal_hands2),
                CARD_ATTRIBUTE_INDEX,
            ),
        ).toBe(0)
    })

    test('multiple ideal patterns', () => {
        const hand = [86988864, 6850209]
        const ideal_hands = [
            [86988864, 80181649],
            [86988864, 'any_superType_spell'],
        ]
        expect(
            hand_is_wild(
                hand,
                compile_patterns(ideal_hands),
                CARD_ATTRIBUTE_INDEX,
            ),
        ).toBe(1)
    })

    test('empty hand or empty ideal', () => {
        const hand: number[] = []
        const ideal_hands: number[][] = [[]]
        expect(
            hand_is_wild(
                hand,
                compile_patterns(ideal_hands),
                CARD_ATTRIBUTE_INDEX,
            ),
        ).toBe(1)

        const hand2 = [80181649]
        const ideal_hands2: number[][] = []
        expect(
            hand_is_wild(
                hand2,
                compile_patterns(ideal_hands2),
                CARD_ATTRIBUTE_INDEX,
            ),
        ).toBe(0)
    })
})
