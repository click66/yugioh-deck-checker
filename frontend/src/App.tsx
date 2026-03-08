import { useState, useEffect } from 'react'
import { createJob, getJob, JobStatus } from './services/consistency'
import type { ConsistencyJobResponse } from './services/consistency'
import { useCardDatabase } from './hooks/useCardDatabase'
import { DeckRow } from './components/dca/deck-row'
import { parseYdk } from './services/ydk-import'
import type { DeckLine, Card, Wildcard } from './types/deck'

const loadingMessages = [
    'Shuffling the deck',
    'Drawing opening hands',
    'Consulting the heart of the cards',
    'Simulating thousands of duels',
    'Checking combo consistency',
    'Calculating probabilities',
    'Recreating perfectly quaffed hair',
    'Running probability scenarios',
    "Stacking the deck myself so there's no one else to blame",
    'Postulating a winning strategem',
    'Initiating duel simulation',
    'Calculating player strength',
    'Performing quantum analysis',
]

const wildcardOptions: Wildcard[] = [
    { id: 'any_monster', name: 'Any Monster', wildcard: true },
    { id: 'any_spell', name: 'Any Spell', wildcard: true },
    { id: 'any_trap', name: 'Any Trap', wildcard: true },
]

const DECK_STORAGE_KEY = 'deck'
const HANDS_STORAGE_KEY = 'hands'

export default function App() {
    const [expandedSteps, setExpandedSteps] = useState<{
        [key: number]: boolean
    }>({
        1: true,
        2: false,
        3: false,
    })

    const defaultDeckLine = {
        card: { id: 44362883, name: 'Branded Fusion' },
        count: 1,
        input: 'Branded Fusion',
    }

    const [deck, setDeck] = useState<DeckLine[]>(() => {
        const saved = localStorage.getItem(DECK_STORAGE_KEY)
        if (saved) {
            return JSON.parse(saved)
        }
        return [defaultDeckLine]
    })

    type HandItem = Card | Wildcard

    const [hands, setHands] = useState<HandItem[][]>(() => {
        const saved = localStorage.getItem(HANDS_STORAGE_KEY)
        return saved ? JSON.parse(saved) : []
    })

    const [deckSize, setDeckSize] = useState(40)
    const [showHandModal, setShowHandModal] = useState(false)
    const [newHand, setNewHand] = useState<HandItem[]>([])
    const [job, setJob] = useState<ConsistencyJobResponse | null>(null)
    const [loading, setLoading] = useState(false)
    const [loadingMessage, setLoadingMessage] = useState(
        loadingMessages[Math.floor(Math.random() * loadingMessages.length)],
    )
    const [useWildcards, setUseWildcards] = useState(false)

    useEffect(() => {
        localStorage.setItem(DECK_STORAGE_KEY, JSON.stringify(deck))
    }, [deck])

    useEffect(() => {
        localStorage.setItem(HANDS_STORAGE_KEY, JSON.stringify(hands))
    }, [hands])

    useEffect(() => {
        if (!loading) return
        const interval = setInterval(() => {
            setLoadingMessage(
                loadingMessages[
                    Math.floor(Math.random() * loadingMessages.length)
                ],
            )
        }, 5000)
        return () => clearInterval(interval)
    }, [loading])

    useEffect(() => {
        const activeJobId = localStorage.getItem('activeJobId')
        if (!activeJobId) {
            return
        }

        setExpandedSteps((prev) => ({ ...prev, 3: true }))

        const resumePoll = async () => {
            setLoading(true)
            const result = await getJob(activeJobId)
            setJob(result)

            if (result.status === JobStatus.COMPLETED) {
                setLoading(false)
                localStorage.removeItem('activeJobId')
            } else {
                setTimeout(resumePoll, 5000)
            }
        }

        resumePoll()
    }, [])

    const toggleStep = (step: number) => {
        if (step === 3 && loading) {
            return
        }

        setExpandedSteps((prev) => ({ ...prev, [step]: !prev[step] }))
    }

    const parseDeck = () => {
        const cleaned = deck.filter((d) => d.card !== null)

        setDeck(cleaned)
        setHands((prev) =>
            prev
                .map((h) =>
                    h.filter((c) => cleaned.some((d) => d.card?.id === c.id)),
                )
                .filter((h) => h.length > 0),
        )
        setJob(null)
        setExpandedSteps({ 1: false, 2: true, 3: false })
    }

    const addHand = () => {
        if (newHand.length > 0) {
            setHands([...hands, newHand])
            setNewHand([])
            setShowHandModal(false)
            setExpandedSteps((prev) => ({ ...prev, 3: true }))
        }
    }

    const clearDeck = () => setDeck([])

    const runAnalysis = async () => {
        if (deck.length === 0 || hands.length === 0) {
            return
        }

        const validatedDeck = deck.filter((d) => d.card !== null)

        setLoading(true)
        setExpandedSteps((prev) => ({ ...prev, 2: false }))

        const payload = {
            deckcount: deckSize,
            names: validatedDeck.map((d) => `${d.card!.id}`),
            ratios: validatedDeck.map((d) => Number(d.count) || 0),
            ideal_hands: hands.map((hand) =>
                hand.map((c) => (typeof c.id === 'number' ? `${c.id}` : c.id)),
            ),
            num_hands: hands.length,
            use_wildcards: useWildcards,
        }

        const jobResp = await createJob(payload)
        setJob(jobResp)

        if (jobResp.jobId) {
            localStorage.setItem('activeJobId', jobResp.jobId)
        }

        const poll = async () => {
            if (!jobResp.jobId) {
                return
            }

            const result = await getJob(jobResp.jobId)
            setJob(result)

            if (result.status === JobStatus.COMPLETED) {
                setLoading(false)
                localStorage.removeItem('activeJobId')
            } else {
                setTimeout(poll, 5000)
            }
        }
        poll()
    }

    const deckProps = {
        deck,
        setDeck,
        deckSize,
        setDeckSize,
        parseDeck,
        clearDeck,
    }
    const handProps = {
        hands,
        setHands,
        newHand,
        setNewHand,
        showHandModal,
        setShowHandModal,
        addHand,
        deck,
    }
    const analysisProps = { hands, job, loading, loadingMessage, runAnalysis }

    return (
        <>
            <div className="bg-gray-50 py-10">
                <div className="max-w-3xl mx-auto space-y-6">
                    <h1 className="text-3xl font-semibold text-center text-gray-800">
                        Yu-Gi-Oh Deck Consistency Analysis
                    </h1>
                    <p className="px-2">
                        A tool for estimating a deck's consistency at drawing
                        specific hands.
                    </p>
                    <p className="px-2">
                        Configure your deck and create a set of ideal hands; the
                        analysis will generate 1 million random hands to give an
                        actual result of how often you will open one of your
                        ideal hands.
                    </p>

                    <Step1
                        expanded={expandedSteps[1]}
                        toggle={() => toggleStep(1)}
                        deckProps={deckProps}
                    />
                    <Step2
                        expanded={expandedSteps[2]}
                        toggle={() => toggleStep(2)}
                        handProps={handProps}
                    />
                    <Step3
                        expanded={expandedSteps[3]}
                        toggle={() => toggleStep(3)}
                        analysisProps={analysisProps}
                    >
                        <div className="flex items-center mt-4">
                            <input
                                type="checkbox"
                                id="useWildcards"
                                checked={useWildcards}
                                onChange={(e) =>
                                    setUseWildcards(e.target.checked)
                                }
                                className="mr-2"
                            />
                            <label
                                htmlFor="useWildcards"
                                className="text-sm text-gray-700"
                            >
                                Use wildcards (experimental feature)
                            </label>
                        </div>
                    </Step3>
                </div>
            </div>
            <footer className="w-full bg-gray-100 border-t border-gray-300 mt-10">
                <div className="max-w-3xl mx-auto text-center text-gray-700 space-y-1 py-4 px-3 text-sm">
                    <p>
                        Adapted from code championed and shared by{' '}
                        <a
                            href="https://www.youtube.com/watch?v=-9sCMYEIeq8"
                            className="text-blue-600 hover:underline"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Lucas Sacco
                        </a>
                        .
                    </p>
                    <p>Original scripts written by Jeremy Glassman.</p>
                    <p>
                        Shout out to mint and{' '}
                        <a
                            href="https://www.deckcal.cc/"
                            className="text-blue-600 hover:underline"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            deckcal.cc
                        </a>{' '}
                        for some design inspiration.
                    </p>
                </div>
            </footer>
        </>
    )
}

function Panel({ title, expanded, toggle, children, expandable = true }: any) {
    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 text-sm">
            <div
                className={`px-5 py-3 border-b border-gray-200 font-medium text-lg flex justify-between ${expandable ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                onClick={toggle}
            >
                {title}
                <span className="text-gray-400">{expanded ? '−' : '+'}</span>
            </div>
            {expanded && <div className="p-5">{children}</div>}
        </div>
    )
}

function Step1({ expanded, toggle, deckProps }: any) {
    const { cards: cardDatabase } = useCardDatabase()
    const { deck, setDeck, deckSize, setDeckSize, parseDeck, clearDeck } =
        deckProps

    const updateRow = (
        index: number,
        field: 'input' | 'count',
        value: string,
    ) => {
        const updated = [...deck]

        if (field === 'count') {
            updated[index].count = value === '' ? '' : Number(value)
        } else {
            updated[index].input = value
            updated[index].card = null
        }

        setDeck(updated)
    }

    const selectSuggestion = (index: number, card: Card) => {
        const updated = [...deck]
        updated[index].card = card
        updated[index].input = card.name
        setDeck(updated)
    }

    const addRow = () => setDeck([...deck, { card: null, count: 1, input: '' }])
    const removeRow = (i: number) =>
        setDeck(deck.filter((_: any, idx: number) => idx !== i))

    const enteredTotal = deck.reduce(
        (acc: number, d: any) => acc + (Number(d.count) || 0),
        0,
    )
    const blankCount = Math.max(deckSize - enteredTotal, 0)

    function importYdkFile(file: File) {
        const reader = new FileReader()

        reader.onload = () => {
            if (!reader.result) {
                return
            }

            const countMap = parseYdk(reader.result as string)

            const importedDeck: DeckLine[] = Array.from(countMap.entries())
                .map(([id, count]) => {
                    const card = cardDatabase.find((c) => c.id === id)

                    if (!card) return undefined

                    return {
                        card,
                        input: card.name,
                        count: count as number | '',
                    }
                })
                .filter((c) => c !== undefined)

            setDeck(importedDeck)
        }

        reader.readAsText(file)
    }

    return (
        <Panel
            title="Step 1 — Configure Deck"
            expanded={expanded}
            toggle={toggle}
        >
            <div className="mb-4">
                <label className="text-sm text-gray-600">Deck size</label>
                <input
                    type="number"
                    value={deckSize}
                    onChange={(e) => setDeckSize(Number(e.target.value))}
                    className="ml-3 w-24 border border-gray-200 rounded px-2 py-1"
                />
            </div>

            <div className="space-y-3">
                <div className="flex gap-3 items-center bg-gray-100 border border-dashed border-gray-300 rounded-lg px-3 py-2 text-gray-500">
                    <div className="w-16 text-center">{blankCount}</div>
                    <div className="flex-1 italic">Blank Card</div>
                </div>

                {deck.map((row: DeckLine, i: number) => (
                    <DeckRow
                        key={i}
                        row={row}
                        index={i}
                        updateRow={updateRow}
                        selectSuggestion={selectSuggestion}
                        removeRow={removeRow}
                    />
                ))}

                <div className="flex gap-3 pt-3 items-center">
                    <button
                        onClick={addRow}
                        className="px-4 py-2 bg-gray-200 rounded"
                    >
                        Add Card
                    </button>
                    <button
                        onClick={parseDeck}
                        className="px-5 py-2 bg-blue-500 text-white rounded"
                    >
                        Next
                    </button>
                    <button
                        onClick={clearDeck}
                        className="px-4 py-2 bg-red-500 text-white rounded"
                    >
                        Clear Deck
                    </button>
                    <label className="px-4 py-2 bg-green-500 text-white rounded cursor-pointer hover:bg-green-600">
                        Import YDK
                        <input
                            type="file"
                            accept=".ydk,text/plain"
                            onChange={(e) =>
                                e.target.files?.[0] &&
                                importYdkFile(e.target.files[0])
                            }
                            className="hidden"
                        />
                    </label>
                </div>
            </div>
        </Panel>
    )
}

function Step2({ expanded, toggle, handProps }: any) {
    const {
        hands,
        setHands,
        newHand,
        setNewHand,
        showHandModal,
        setShowHandModal,
        addHand,
        deck,
    } = handProps
    const selectableDeck = deck.filter((d: DeckLine) => d.card !== null)

    return (
        <Panel
            title="Step 2 — Define Ideal Hands"
            expanded={expanded}
            toggle={toggle}
        >
            <button
                onClick={() => setShowHandModal(true)}
                className="mb-4 px-4 py-2 bg-green-500 text-white rounded "
            >
                Add Ideal Hand
            </button>
            {hands.length === 0 && (
                <div className="text-gray-500 text-sm">
                    No ideal hands defined yet.
                </div>
            )}
            <div className="space-y-2">
                {hands.map((hand: Card[], i: number) => (
                    <div
                        key={i}
                        className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 flex justify-between"
                    >
                        <span>{hand.map((c) => c.name).join(', ')}</span>
                        <button
                            onClick={() =>
                                setHands(
                                    hands.filter(
                                        (_: any, idx: number) => idx !== i,
                                    ),
                                )
                            }
                            className="text-red-400 text-sm "
                        >
                            remove
                        </button>
                    </div>
                ))}
            </div>

            {showHandModal && (
                <div
                    className="fixed inset-0 bg-black/30 flex items-center justify-center"
                    onClick={() => setShowHandModal(false)}
                >
                    <div
                        className="bg-white rounded-xl shadow-lg p-6 w-full max-w-xl"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 className="text-lg font-medium mb-4">
                            Select Cards
                        </h3>

                        {newHand.length > 0 && (
                            <div className="mb-3 text-sm text-gray-700">
                                Selected:{' '}
                                {newHand.map((card: Card, idx: number) => (
                                    <span
                                        key={idx}
                                        className="inline-flex items-center mr-1"
                                    >
                                        {card.name}
                                        <button
                                            type="button"
                                            onClick={() =>
                                                setNewHand([
                                                    ...newHand.slice(0, idx),
                                                    ...newHand.slice(idx + 1),
                                                ])
                                            }
                                            className="ml-1 text-red-500 "
                                        >
                                            ×
                                        </button>
                                    </span>
                                ))}
                            </div>
                        )}

                        <div className="mb-4">
                            <div className="text-sm text-gray-600 mb-2">
                                Wildcards
                            </div>
                            <div className="flex gap-2 flex-wrap">
                                {wildcardOptions.map((wc) => (
                                    <button
                                        key={wc.id}
                                        type="button"
                                        onClick={() =>
                                            setNewHand([...newHand, wc])
                                        }
                                        className="px-3 py-2 rounded-lg border border-purple-200 bg-purple-50 hover:bg-purple-100"
                                    >
                                        {wc.name} (
                                        {
                                            newHand.filter(
                                                (c: any) => c.id === wc.id,
                                            ).length
                                        }
                                        )
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-80 overflow-y-auto">
                            {selectableDeck.map((d: { card: Card }) => (
                                <button
                                    key={d.card.id}
                                    type="button"
                                    onClick={() =>
                                        setNewHand([...newHand, d.card])
                                    }
                                    className="px-3 py-2 rounded-lg border border-gray-200 hover:bg-gray-50"
                                >
                                    {d.card.name} (
                                    {
                                        newHand.filter(
                                            (c: Card) => c === d.card,
                                        ).length
                                    }
                                    )
                                </button>
                            ))}
                        </div>

                        <div className="flex justify-end gap-3 mt-5">
                            <button
                                onClick={() => setShowHandModal(false)}
                                className="px-4 py-2 bg-gray-200 rounded "
                            >
                                Cancel
                            </button>
                            <button
                                onClick={addHand}
                                disabled={newHand.length === 0}
                                className="px-4 py-2 bg-blue-500 text-white rounded  disabled:opacity-50"
                            >
                                Save
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </Panel>
    )
}

function Step3({ expanded, toggle, analysisProps, children }: any) {
    const { hands, job, loading, loadingMessage, runAnalysis } = analysisProps
    const p5 = job?.result?.value ? parseFloat(job.result.value) : null
    const p6 = job?.result?.value_6 ? parseFloat(job.result.value_6) : null

    return (
        <Panel
            title="Step 3 — Run Analysis"
            expanded={expanded}
            toggle={toggle}
            expandable={!loading}
        >
            {!loading && (
                <button
                    onClick={runAnalysis}
                    disabled={hands.length === 0}
                    className="px-5 py-2 bg-purple-500 text-white rounded disabled:opacity-50 "
                >
                    Run Analysis
                </button>
            )}

            {children}

            {loading && (
                <div className="flex flex-col items-center gap-4 py-6">
                    <div className="w-10 h-10 border-4 border-purple-400 border-t-transparent rounded-full animate-spin"></div>
                    <div className="text-gray-600 text-sm">
                        {loadingMessage}
                    </div>
                </div>
            )}

            {p5 !== null && p6 !== null && (
                <>
                    <p className="text-center">
                        Analysis complete; the probabilities of opening one of
                        your ideal hands are:
                    </p>
                    <div className="mt-4 flex flex-col sm:flex-row gap-4">
                        <div className="flex-1 p-4 border rounded-lg bg-white shadow text-center">
                            <div className="text-gray-500 mb-1">
                                5-card hand
                            </div>
                            <div className="text-2xl font-bold text-purple-600">
                                {(p5 * 100).toFixed(2)}%
                            </div>
                        </div>
                        <div className="flex-1 p-4 border rounded-lg bg-white shadow text-center">
                            <div className="text-gray-500 mb-1">
                                6-card hand
                            </div>
                            <div className="text-2xl font-bold text-purple-600">
                                {(p6 * 100).toFixed(2)}%
                            </div>
                        </div>
                    </div>
                </>
            )}
        </Panel>
    )
}
