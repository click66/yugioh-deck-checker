import { useState, useEffect, useRef } from 'react'
import { createJob, getJob, JobStatus } from './services/consistency'
import type { ConsistencyJobResponse } from './services/consistency'
import { useCardDatabase } from './hooks/useCardDatabase'
import { DeckRow } from './components/dca/deck-row'
import { parseYdk } from './services/ydk-import'
import type { DeckLine, Card, Wildcard } from './types/deck'
import { InformationCircleIcon } from '@heroicons/react/16/solid'

function InfoTooltip({ content }: { content: string }) {
    const [visible, setVisible] = useState(false)

    return (
        <div className="relative inline-block ml-1">
            <InformationCircleIcon
                className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-pointer"
                onMouseEnter={() => setVisible(true)}
                onMouseLeave={() => setVisible(false)}
                onClick={() => setVisible((v) => !v)}
            />
            {visible && (
                <div className="absolute z-10 w-64 p-2 bg-gray-700 text-white text-xs rounded shadow-lg mt-1 -left-32 sm:left-0">
                    {content}
                </div>
            )}
        </div>
    )
}
const loadingMessages = [
    'Shuffling the deck',
    'Drawing opening hands',
    'Consulting the heart of the cards',
    'Simulating thousands of duels',
    'Checking combo consistency',
    'Calculating probabilities',
    'Recreating perfectly quaffed hair',
    'Running probability scenarios',
    'Stacking the deck',
    'Postulating a winning strategem',
    'Initiating duel simulation',
    'Calculating player strength',
    'Performing quantum duel analysis',
    'Scanning for dead draws',
    'Activating Pot of Greed',
    'Scanning for pathetic cards',
    'Calculating brick percentages',
    'Linking into the VRAINS',
    'Simulating first turn plays',
    'Searching for Habikiri',
    'Running Monte Carlo simulation',
    'Evaluating effects of deck thinning',
]

const wildcardOptions: Wildcard[] = [
    { id: 'any_superType_monster', name: 'Any Monster', wildcard: true },
    { id: 'any_superType_spell', name: 'Any Spell', wildcard: true },
    { id: 'any_superType_trap', name: 'Any Trap', wildcard: true },
]

const DECK_STORAGE_KEY = 'deck'
const HANDS_STORAGE_KEY = 'hands'
export default function App() {
    const pollTimeout = useRef<number | null>(null)

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
        loadingMessages[Math.floor(Math.random() * loadingMessages.length)] +
            '...',
    )
    const [error, setError] = useState<string | null>(null)
    const [useGambling, setUseGambling] = useState(false)

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
                ] + '...',
            )
        }, 5000)
        return () => clearInterval(interval)
    }, [loading])

    useEffect(() => {
        const activeJobId = localStorage.getItem('activeJobId')
        if (!activeJobId) return

        setExpandedSteps((prev) => ({ ...prev, 3: true }))
        setLoading(true)

        pollJob(activeJobId)
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

    const pollJob = async (jobId: string) => {
        const result = await getJob(jobId)

        if (!result) {
            setLoading(false)
            localStorage.removeItem('activeJobId')
            return
        }

        setJob(result)

        if (result.status === JobStatus.COMPLETED) {
            setLoading(false)
            localStorage.removeItem('activeJobId')
        } else if (result.status === JobStatus.FAILED) {
            setLoading(false)
            setError(result.error?.detail || 'Job failed')
            localStorage.removeItem('activeJobId')
        } else {
            pollTimeout.current = setTimeout(() => pollJob(jobId), 5000)
        }
    }

    const cancelAnalysis = () => {
        if (pollTimeout.current) {
            clearTimeout(pollTimeout.current)
            pollTimeout.current = null
        }
        setLoading(false)
        setJob(null)
        localStorage.removeItem('activeJobId')
    }

    const runAnalysis = async () => {
        if (deck.length === 0 || hands.length === 0) {
            return
        }

        const validatedDeck = deck.filter((d) => d.card !== null)

        setError(null)
        setLoading(true)
        setExpandedSteps((prev) => ({ ...prev, 2: false }))

        const payload = {
            deckcount: deckSize,
            names: validatedDeck.map((d) => `${d.card!.id}`),
            ratios: validatedDeck.map((d) => Number(d.count) || 0),
            ideal_hands: hands.map((hand) =>
                hand.map((c) => (typeof c.id === 'number' ? `${c.id}` : c.id)),
            ),
            num_hands: 1_000_000,
            use_gambling: useGambling,
        }

        const jobResp = await createJob(payload)
        setJob(jobResp)

        if (jobResp.jobId) {
            localStorage.setItem('activeJobId', jobResp.jobId)
            pollJob(jobResp.jobId)
        }
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
    const analysisProps = {
        hands,
        job,
        loading,
        loadingMessage,
        runAnalysis,
        error,
        useGambling,
        setUseGambling,
        cancelAnalysis,
        deck,
        deckSize,
    }

    return (
        <>
            <div className="bg-gray-50 py-10">
                <div className="max-w-3xl mx-auto space-y-6">
                    <h1 className="text-3xl font-semibold text-center text-gray-800">
                        Yu-Gi-Oh! Deck Analysis
                    </h1>
                    <p className="px-2">
                        A tool for estimating a deck's consistency at drawing
                        specific hands.
                    </p>
                    <p className="px-2">
                        Configure your deck and create a set of ideal hands. The
                        simulator will generate 1 million random hands (both as
                        a 5-card hand and with a 6th card drawn) to give an
                        actual result of how often you will open one of them.
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
                        setExpandedSteps={setExpandedSteps}
                    />
                    <Step3
                        expanded={expandedSteps[3]}
                        toggle={() => toggleStep(3)}
                        analysisProps={analysisProps}
                    />
                </div>
            </div>
            <footer className="w-full bg-gray-100 border-t border-gray-300 mt-10">
                <div className="max-w-3xl mx-auto text-center text-gray-700 space-y-1 py-4 px-3 text-sm">
                    <p className="mb-4">
                        This is a beta tool and as such bugs may be present. The
                        simulator is naive and is not guaranteed to play hands
                        perfectly. If you find any issues or have suggestions
                        for improvement, feel free to{' '}
                        <a
                            className="text-blue-600 hover:underline"
                            href="mailto:click66@gmail.com"
                        >
                            email me
                        </a>
                        .
                    </p>
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

    const [showPasteModal, setShowPasteModal] = useState(false)
    const [pastedYdk, setPastedYdk] = useState('')

    const updateRow = (
        index: number,
        field: 'input' | 'count',
        value: string,
    ) => {
        const updated = [...deck]
        if (field === 'count')
            updated[index].count = value === '' ? '' : Number(value)
        else {
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
            if (!reader.result) return
            parseYdkContent(reader.result as string)
        }
        reader.readAsText(file)
    }

    function parseYdkContent(ydkString: string) {
        const countMap = parseYdk(ydkString)

        const importedDeck: DeckLine[] = Array.from(countMap.entries())
            .map(([id, count]) => {
                const card = cardDatabase.find((c) => c.id === id)
                if (!card) return undefined
                return { card, input: card.name, count: count as number | '' }
            })
            .filter((c) => c !== undefined)

        setDeck(importedDeck)
        setShowPasteModal(false)
        setPastedYdk('')
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
                    value={deckSize.toString()}
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
                        cardDatabase={cardDatabase}
                    />
                ))}

                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 pt-3">
                    <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                        <button
                            onClick={addRow}
                            className="w-full sm:w-auto px-4 py-2 bg-gray-200 rounded"
                        >
                            Add Card
                        </button>
                        <button
                            onClick={clearDeck}
                            className="w-full sm:w-auto px-4 py-2 bg-red-500 text-white rounded"
                        >
                            Clear Deck
                        </button>

                        <div className="flex flex-row gap-3 w-full sm:w-auto">
                            <label className="w-1/2 sm:w-auto px-4 py-2 bg-green-500 text-white rounded cursor-pointer hover:bg-green-600 text-center">
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
                            <button
                                className="w-1/2 sm:w-auto px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
                                onClick={() => setShowPasteModal(true)}
                            >
                                Copy/Paste YDK
                            </button>
                        </div>
                    </div>

                    <div className="order-2 sm:order-2 sm:ml-auto w-full sm:w-auto">
                        <button
                            onClick={parseDeck}
                            className="px-5 py-2 bg-blue-500 text-white rounded w-full sm:w-auto"
                        >
                            Next
                        </button>
                    </div>
                </div>
            </div>

            {showPasteModal && (
                <div
                    className="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-50"
                    onClick={() => setShowPasteModal(false)}
                >
                    <div
                        className="bg-white rounded-xl shadow-lg p-6 w-full max-w-xl flex flex-col gap-4 max-h-[80vh] overflow-y-auto"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 className="text-lg font-semibold mb-2 text-center">
                            Paste YDK Contents
                        </h3>
                        <textarea
                            value={pastedYdk}
                            onChange={(e) => setPastedYdk(e.target.value)}
                            className="w-full h-64 border border-gray-300 rounded p-2 text-sm"
                        />
                        <div className="flex justify-end gap-3 mt-2">
                            <button
                                onClick={() => setShowPasteModal(false)}
                                className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => parseYdkContent(pastedYdk)}
                                disabled={!pastedYdk.trim()}
                                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                            >
                                Import
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </Panel>
    )
}

function Step2({ expanded, toggle, handProps, setExpandedSteps }: any) {
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

    const selectableDeck = deck
        .filter((d: DeckLine) => d.card !== null)
        .sort((a: DeckLine, b: DeckLine) =>
            a.card!.name.localeCompare(b.card!.name),
        )

    const blankMessage = hands.length === 0 && (
        <div className="text-gray-500 text-sm mb-2">
            No ideal hands defined yet.
        </div>
    )

    const goNext = () => {
        toggle()
        setExpandedSteps((prev: any) => ({ ...prev, 3: true }))
    }

    return (
        <Panel
            title="Step 2 — Define Ideal Hands"
            expanded={expanded}
            toggle={toggle}
        >
            {blankMessage}

            <div className="space-y-2 mb-4">
                {hands.map((hand: (Card | Wildcard)[], i: number) => (
                    <div
                        key={i}
                        className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 flex flex-wrap items-center justify-between gap-2"
                    >
                        <div className="flex flex-wrap gap-2">
                            {hand.map((c, idx) => {
                                const isWildcard = (c as Wildcard).wildcard
                                return (
                                    <span
                                        key={idx}
                                        className={`inline-flex items-center px-2 py-1 rounded-full text-sm font-medium ${
                                            isWildcard
                                                ? 'bg-purple-100 text-purple-700'
                                                : 'bg-gray-200 text-gray-800'
                                        }`}
                                    >
                                        {c.name}
                                    </span>
                                )
                            })}
                        </div>
                        <button
                            onClick={() =>
                                setHands(
                                    hands.filter(
                                        (_: any, idx2: number) => idx2 !== i,
                                    ),
                                )
                            }
                            className="px-2 py-1 text-sm bg-red-400 text-white rounded hover:bg-red-500"
                        >
                            Remove
                        </button>
                    </div>
                ))}
            </div>

            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 pt-3 w-full">
                <button
                    onClick={() => setShowHandModal(true)}
                    className="w-full sm:w-auto px-4 py-2 bg-green-500 text-white rounded"
                >
                    Add Ideal Hand
                </button>

                <button
                    onClick={goNext}
                    disabled={hands.length === 0}
                    className="w-full sm:w-auto px-5 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
                >
                    Next
                </button>
            </div>

            {showHandModal && (
                <div
                    className="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-50"
                    onClick={() => setShowHandModal(false)}
                >
                    <div
                        className="bg-white rounded-xl shadow-lg p-6 w-full max-w-xl flex flex-col gap-4 max-h-[80vh] overflow-y-auto"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 className="text-lg font-semibold mb-2 text-center">
                            Select Cards
                        </h3>

                        <div className="flex flex-wrap gap-2 mb-2 min-h-[2rem]">
                            {newHand.map(
                                (card: Card | Wildcard, idx: number) => (
                                    <div
                                        key={idx}
                                        className="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded shadow-sm text-sm"
                                    >
                                        {card.name} (
                                        {
                                            newHand.filter(
                                                (c: Card) => c === card,
                                            ).length
                                        }
                                        )
                                        <button
                                            type="button"
                                            onClick={() =>
                                                setNewHand([
                                                    ...newHand.slice(0, idx),
                                                    ...newHand.slice(idx + 1),
                                                ])
                                            }
                                            className="text-red-500 hover:text-red-700"
                                        >
                                            ×
                                        </button>
                                    </div>
                                ),
                            )}
                        </div>

                        {/* Wildcards */}
                        <div className="mb-4">
                            <div className="text-sm text-gray-600 mb-1 font-medium">
                                Wildcards
                            </div>
                            <div className="grid grid-cols-3 gap-2">
                                {wildcardOptions.map((wc) => (
                                    <button
                                        key={wc.id}
                                        type="button"
                                        onClick={() =>
                                            setNewHand([...newHand, wc])
                                        }
                                        className="px-3 py-2 rounded-lg border border-purple-200 bg-purple-50 hover:bg-purple-100 text-sm font-medium"
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

                        <div className="mb-4">
                            <div className="text-sm text-gray-600 mb-1 font-medium">
                                Deck Cards
                            </div>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                {selectableDeck.map((d: { card: Card }) => (
                                    <button
                                        key={d.card.id}
                                        type="button"
                                        onClick={() =>
                                            setNewHand([...newHand, d.card])
                                        }
                                        className="px-3 py-2 rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100 text-sm text-gray-700"
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
                        </div>

                        <div className="flex justify-end gap-3 mt-2">
                            <button
                                onClick={() => setShowHandModal(false)}
                                className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={addHand}
                                disabled={newHand.length === 0}
                                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
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
    const {
        hands,
        job,
        loading,
        loadingMessage,
        runAnalysis,
        error,
        useGambling,
        setUseGambling,
        cancelAnalysis,
        deck,
        deckSize,
    } = analysisProps

    const totalRatios = deck.reduce(
        (sum: number, d: any) => sum + (Number(d.count) || 0),
        0,
    )

    const isDeckValid = totalRatios <= deckSize
    const canRunAnalysis = hands.length > 0 && isDeckValid

    const { cards: cardDatabase } = useCardDatabase()

    return (
        <Panel
            title="Step 3 — Run Analysis"
            expanded={expanded}
            toggle={toggle}
            expandable={!loading}
        >
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 mb-4">
                {!loading && (
                    <>
                        <div className="flex items-center gap-2 order-0 sm:order-2">
                            <label className="flex items-center gap-2 text-gray-700 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={useGambling}
                                    onChange={(e) =>
                                        setUseGambling(e.target.checked)
                                    }
                                    className="w-4 h-4"
                                />
                                Use gambling?
                            </label>

                            <InfoTooltip content="Simulate cards that allow drawing extra cards, accounting for if those cards have discard requirements (e.g. Allure of Darkness). This may increase overall processing time and not all gambling cards may be supported." />
                        </div>

                        <button
                            onClick={runAnalysis}
                            disabled={!canRunAnalysis}
                            className="px-5 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
                        >
                            Run Analysis
                        </button>
                    </>
                )}

                {loading && (
                    <button
                        onClick={cancelAnalysis}
                        className="px-5 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                    >
                        Cancel Analysis
                    </button>
                )}
            </div>

            {!isDeckValid && (
                <div className="mb-4 p-3 border border-red-300 bg-red-50 text-red-700 rounded">
                    Total card counts exceed deck size ({totalRatios} /{' '}
                    {deckSize})
                </div>
            )}

            {children}

            {error && (
                <div className="mt-4 p-3 border border-red-300 bg-red-50 text-red-700 rounded">
                    {error}
                </div>
            )}

            {loading && (
                <div className="flex flex-col items-center gap-4 py-6">
                    <div className="w-10 h-10 border-4 border-purple-400 border-t-transparent rounded-full animate-spin"></div>
                    <div className="text-gray-600 text-sm">
                        {loadingMessage}
                    </div>
                </div>
            )}

            {job?.result && <Results job={job} cardDatabase={cardDatabase} />}
        </Panel>
    )
}

interface ResultsProps {
    job: ConsistencyJobResponse
    cardDatabase: Card[]
}

export function Results({ job, cardDatabase }: ResultsProps) {
    if (!job?.result) return null

    const numHands = 1_000_000
    const usedGambling = job.result.used_gambling

    const p5 = parseFloat(job.result.p5 || '0')
    const p6 = parseFloat(job.result.p6 || '0')
    const p5WithGambling = parseFloat(job.result.p5_with_gambling || '0')
    const p6WithGambling = parseFloat(job.result.p6_with_gambling || '0')

    const matchedCounts5 = job.result.matched_pattern_counts_5 || {}
    const multiMatch5Count = Object.entries(matchedCounts5)
        .filter(([matches, _]) => Number(matches) > 1)
        .reduce((sum, [, count]) => sum + Number(count), 0)

    const matchedCounts6 = job.result.matched_pattern_counts_6 || {}
    const multiMatch6Count = Object.entries(matchedCounts6)
        .filter(([matches, _]) => Number(matches) > 1)
        .reduce((sum, [, count]) => sum + Number(count), 0)

    const rescued5 = parseInt(job.result.rescued_5 || '0', 10)
    const rescued6 = parseInt(job.result.rescued_6 || '0', 10)

    const totalAttempts5 = parseInt(job.result.gamble_attempted_5 || '0', 10)
    const totalAttempts6 = parseInt(job.result.gamble_attempted_6 || '0', 10)

    const totalFailed5 = parseInt(job.result.gamble_failed_5 || '0', 10)
    const totalFailed6 = parseInt(job.result.gamble_failed_6 || '0', 10)

    const usefulGambles5 = job.result.useful_gambles_5 || {}
    const usefulGambles6 = job.result.useful_gambles_6 || {}
    const gambleSeen5 = job.result.gamble_seen_5 || {}
    const gambleSeen6 = job.result.gamble_seen_6 || {}

    // const nearMissCounts = job.result.near_miss_counts || {}
    // const blockingCardCounts = job.result.blocking_card_counts || {}
    // const idealHandCounts = job.result.ideal_hand_counts || {}

    const getCardName = (id: string) =>
        cardDatabase.find((c) => `${c.id}` === id)?.name || id

    const gamblingStats = [
        {
            title: '5-card hand',
            rescued: rescued5,
            attempts: totalAttempts5,
            failed: totalFailed5,
            seen: gambleSeen5,
            usefulGambles: usefulGambles5,
        },
        {
            title: '6-card hand',
            rescued: rescued6,
            attempts: totalAttempts6,
            failed: totalFailed6,
            seen: gambleSeen6,
            usefulGambles: usefulGambles6,
        },
    ]

    // const renderTopCards = (
    //     counts: Record<string, string | number>,
    //     title: string,
    //     tooltip: string,
    // ) => {
    //     const entries = Object.entries(counts)
    //         .map(([id, count]) => {
    //             const name = getCardName(id)
    //             if (!name) return null
    //             const pct = (Number(count) / numHands) * 100
    //             return { name, pct }
    //         })
    //         .filter(Boolean) as { name: string; pct: number }[]

    //     const top3 = entries.sort((a, b) => b.pct - a.pct).slice(0, 3)

    //     if (top3.length === 0) return null

    //     return (
    //         <div className="mb-4">
    //             <div className="font-medium mb-1">{title}</div>
    //             <div className="text-xs text-gray-400 mt-1">{tooltip}</div>
    //             <div className="text-sm text-gray-700">
    //                 {top3.map((c) => (
    //                     <div key={c.name}>
    //                         {c.name}: {c.pct.toFixed(2)}%
    //                     </div>
    //                 ))}
    //             </div>
    //         </div>
    //     )
    // }

    return (
        <>
            <hr className="w-[70%] border-t border-gray-300 mx-auto my-6" />
            <p className="text-center mb-4">
                Analysis complete; in {numHands.toLocaleString()} hands, the
                probability of opening one of your ideal hands was:
            </p>

            <div className="mt-4 flex flex-col sm:flex-row gap-4">
                <div className="flex-1 p-6 border rounded-lg bg-white shadow text-center">
                    <div className="text-gray-500 mb-1">5-card hand</div>
                    <div className="text-3xl font-bold text-purple-600">
                        {(p5 * 100).toFixed(2)}%
                    </div>
                    <div className="text-gray-400 text-sm mt-2">
                        Matched multiple hands:{' '}
                        {((multiMatch5Count / numHands) * 100).toFixed(2)}%
                    </div>
                    {usedGambling && (
                        <div className="text-gray-400 text-sm mt-2">
                            With gambling: {(p5WithGambling * 100).toFixed(2)}%
                        </div>
                    )}
                </div>
                <div className="flex-1 p-6 border rounded-lg bg-white shadow text-center">
                    <div className="text-gray-500 mb-1">6-card hand</div>
                    <div className="text-3xl font-bold text-purple-600">
                        {(p6 * 100).toFixed(2)}%
                    </div>
                    <div className="text-gray-400 text-sm mt-2">
                        Matched multiple hands:{' '}
                        {((multiMatch6Count / numHands) * 100).toFixed(2)}%
                    </div>
                    {usedGambling && (
                        <div className="text-gray-400 text-sm mt-2">
                            With gambling: {(p6WithGambling * 100).toFixed(2)}%
                        </div>
                    )}
                </div>
            </div>

            {/*<div className="mt-6">
                {renderTopCards(
                    idealHandCounts,
                    'Most Helpful Cards',
                    'Percentage of hands where this card appeared in a hand that matched your ideal hand.',
                )}
                {renderTopCards(
                    blockingCardCounts,
                    'Most Dead Draws',
                    'Percentage of hands where this card was in your hand but prevented you from completing an ideal hand.',
                )}
                {renderTopCards(
                    nearMissCounts,
                    'Most Commonly Missing',
                    'Percentage of hands where this card was not in your hand but could have completed an ideal hand.',
                )}
            </div>*/}

            {usedGambling && (
                <div className="mt-6 space-y-4">
                    {gamblingStats.map((stat) => {
                        const gambledPercent = (
                            (stat.attempts / numHands) *
                            100
                        ).toFixed(2)
                        const rescuedPercent = (
                            (stat.rescued / stat.attempts || 1) * 100
                        ).toFixed(2)
                        const failedPercent = (
                            (stat.failed / stat.attempts || 1) * 100
                        ).toFixed(2)

                        return (
                            <div
                                key={stat.title}
                                className="p-4 border rounded-lg bg-white shadow"
                            >
                                <div className="text-gray-600 font-medium mb-2">
                                    {stat.title} Gambling Stats
                                </div>
                                {stat.attempts > 0 ? (
                                    <>
                                        <div className="flex flex-col sm:flex-row sm:gap-6 text-sm text-gray-700 mb-2">
                                            <div>
                                                Gambled on {gambledPercent}% of
                                                hands; of which:
                                            </div>
                                            <div>
                                                {rescuedPercent}% were rescued
                                            </div>
                                            <div>{failedPercent}% failed</div>
                                        </div>

                                        <div className="text-gray-500 text-sm font-medium mb-1">
                                            Individual Cards:
                                        </div>
                                        <div className="flex flex-col gap-1 text-sm text-gray-700">
                                            {Object.entries(stat.seen).map(
                                                ([cardId, val]) => {
                                                    const seen = parseInt(
                                                        val,
                                                        10,
                                                    )
                                                    const rescued = parseInt(
                                                        stat.usefulGambles[
                                                            cardId
                                                        ] || '0',
                                                        10,
                                                    )
                                                    const seenPct = (
                                                        (seen / numHands) *
                                                        100
                                                    ).toFixed(2)
                                                    const rescuedPct = (
                                                        (rescued / seen) *
                                                        100
                                                    ).toFixed(2)
                                                    return (
                                                        <div
                                                            key={cardId}
                                                            className="flex justify-between"
                                                        >
                                                            <div>
                                                                {getCardName(
                                                                    cardId,
                                                                )}
                                                            </div>
                                                            <div>
                                                                Seen in{' '}
                                                                {seenPct}% of
                                                                hands; success
                                                                rate:{' '}
                                                                {rescuedPct}%
                                                            </div>
                                                        </div>
                                                    )
                                                },
                                            )}
                                        </div>
                                    </>
                                ) : (
                                    <div className="flex flex-col sm:flex-row sm:gap-6 text-sm text-gray-700 mb-2">
                                        No gambling was attempted or no gambling
                                        cards were seen.
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>
            )}
        </>
    )
}
