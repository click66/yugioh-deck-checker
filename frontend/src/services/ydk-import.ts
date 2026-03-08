export function parseYdk(text: string): Map<number, number> {
    const lines = text.split(/\r?\n/).map((l) => l.trim())

    let inMain = false
    const ids: number[] = []

    for (const line of lines) {
        if (line.startsWith('#main')) {
            inMain = true
            continue
        }

        if (line.startsWith('#') || line.startsWith('!')) {
            if (line !== '#main') inMain = false
            continue
        }

        if (inMain && /^\d+$/.test(line)) {
            ids.push(Number(line))
        }
    }

    const map = new Map<number, number>()

    ids.forEach((id) => {
        map.set(id, (map.get(id) || 0) + 1)
    })

    return map
}
