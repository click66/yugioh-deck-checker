export interface GambleCard {
    draw: number
    discard?: [string, string][]
}

export type GamblingCards = Record<number, GambleCard>

export const GAMBLING_CARDS: GamblingCards = {
    1475311: {
        // Allure of Darkness
        draw: 2,
        discard: [['attribute', 'DARK']],
    },
    70368879: {
        // Upstart Goblin
        draw: 1,
        discard: [],
    },
    20508881: {
        // Radiant Typhoon Vision
        draw: 2,
        discard: [['race', 'Quick-Play']],
    },
    52840267: {
        // Darklord Ixchel
        draw: 2,
        discard: [['archetype', 'Darklord']],
    },
    84211599: {
        // Pot of Prosperity
        draw: 6,
        discard: [],
    },
    49238328: {
        // Pot of Extravagance
        draw: 2,
        discard: [],
    },
    55144522: {
        // Pot of Greed
        draw: 2,
        discard: [],
    },
}
