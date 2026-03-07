import { useState, useEffect } from 'react'
import { createJob, getJob, JobStatus } from './services/consistency'
import type { ConsistencyJobResponse } from './services/consistency'
import { useCardDatabase } from './hooks/useCardDatabase';

type DeckLine = { name: string; count: number | '' }
type Card = string

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

    const defaultDeckLine = { name: 'Branded Fusion', count: 1 }
    const [deck, setDeck] = useState<DeckLine[]>(() => {
        const saved = localStorage.getItem(DECK_STORAGE_KEY)
        return saved ? JSON.parse(saved) : [defaultDeckLine]
    })
    const [hands, setHands] = useState<string[][]>(() => {
        const saved = localStorage.getItem(HANDS_STORAGE_KEY)
        return saved ? JSON.parse(saved) : []
    })

    const [deckSize, setDeckSize] = useState(40)
    const [showHandModal, setShowHandModal] = useState(false)
    const [newHand, setNewHand] = useState<string[]>([])
    const [job, setJob] = useState<ConsistencyJobResponse | null>(null)
    const [loading, setLoading] = useState(false)
    const [loadingMessage, setLoadingMessage] = useState(
        loadingMessages[Math.floor(Math.random() * loadingMessages.length)],
    )

    // Persist deck & hands whenever they change
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

    const toggleStep = (step: number) => {
        if (step === 3 && loading) return
        setExpandedSteps((prev) => ({ ...prev, [step]: !prev[step] }))
    }

    const parseDeck = () => {
        const cleaned = deck
            .filter((d) => d.name.trim() !== '')
            .map((d) => ({
                name: d.name,
                count: Number(d.count) || 0,
            }))
        setDeck(cleaned)
        setHands((prev) =>
            prev
                .map((h) => h.filter((c) => cleaned.some((d) => d.name === c)))
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

    const clearDeck = () => {
        setDeck([])
    }

    const runAnalysis = async () => {
        if (deck.length === 0 || hands.length === 0) return
        setLoading(true)
        setExpandedSteps((prev) => ({ ...prev, 2: false }))

        const names = deck.map((d) => d.name)
        const ratios = deck.map((d) => Number(d.count) || 0)

        const payload = {
            deckcount: deckSize,
            names,
            ratios,
            ideal_hands: hands,
            num_hands: hands.length,
        }

        const jobResp = await createJob(payload)
        setJob(jobResp)

        const poll = async () => {
            if (!jobResp.jobId) return
            const result = await getJob(jobResp.jobId)
            setJob(result)
            if (result.status === JobStatus.COMPLETED) {
                setLoading(false)
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
                    />
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

function Panel({ title, expanded, toggle, children }: any) {
    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div
                className="px-5 py-3 border-b border-gray-200 font-medium text-lg  flex justify-between"
                onClick={toggle}
            >
                {title}
                <span className="text-gray-400">{expanded ? '−' : '+'}</span>
            </div>
            {expanded && <div className="p-5">{children}</div>}
        </div>
    )
}

// ---------------- Step 1 ----------------
function Step1({ expanded, toggle, deckProps }: any) {
    useCardDatabase()
    
    const { deck, setDeck, deckSize, setDeckSize, parseDeck, clearDeck } =
        deckProps

    const updateRow = (
        index: number,
        field: 'name' | 'count',
        value: string,
    ) => {
        const updated = [...deck]
        if (field === 'count')
            updated[index].count = value === '' ? '' : Number(value)
        else updated[index].name = value
        setDeck(updated)
    }

    const addRow = () => setDeck([...deck, { name: '', count: 1 }])
    const removeRow = (i: number) =>
        setDeck(deck.filter((_: any, idx: number) => idx !== i))

    const enteredTotal = deck.reduce(
        (acc: number, d: DeckLine) => acc + (Number(d.count) || 0),
        0,
    )
    const blankCount = Math.max(deckSize - enteredTotal, 0)

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
                    <div
                        key={i}
                        className="flex gap-3 items-center bg-gray-50 border border-gray-200 rounded-lg px-3 py-2"
                    >
                        <input
                            type="number"
                            min={1}
                            max={3}
                            value={row.count}
                            onChange={(e) =>
                                updateRow(i, 'count', e.target.value)
                            }
                            className="w-16 border border-gray-200 rounded px-2 py-1"
                        />
                        <input
                            type="text"
                            value={row.name}
                            placeholder="Card name"
                            onChange={(e) =>
                                updateRow(i, 'name', e.target.value)
                            }
                            className="flex-1 border border-gray-200 rounded px-3 py-1"
                        />
                        <button
                            onClick={() => removeRow(i)}
                            className="px-2 py-1 text-sm bg-red-400 text-white rounded "
                        >
                            Remove
                        </button>
                    </div>
                ))}

                <div className="flex gap-3 pt-3">
                    <button
                        onClick={addRow}
                        className="px-4 py-2 bg-gray-200 rounded "
                    >
                        Add Card
                    </button>
                    <button
                        onClick={parseDeck}
                        className="px-5 py-2 bg-blue-500 text-white rounded "
                    >
                        Next
                    </button>
                    <button
                        onClick={clearDeck}
                        className="px-4 py-2 bg-red-500 text-white rounded "
                    >
                        Clear Deck
                    </button>
                </div>
            </div>
        </Panel>
    )
}

// ---------------- Step 2 ----------------
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
    const selectableDeck = deck.filter((d: DeckLine) => d.name !== 'Blank Card')

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
                {hands.map((hand: string[], i: number) => (
                    <div
                        key={i}
                        className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 flex justify-between"
                    >
                        <span>{hand.join(', ')}</span>
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
                                        {card}
                                        <button
                                            type="button"
                                            onClick={() => {
                                                const copy = [...newHand]
                                                copy.splice(idx, 1)
                                                setNewHand(copy)
                                            }}
                                            className="ml-1 text-red-500 "
                                        >
                                            ×
                                        </button>
                                    </span>
                                ))}
                            </div>
                        )}

                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-80 overflow-y-auto">
                            {selectableDeck.map((d: DeckLine) => (
                                <button
                                    key={d.name + Math.random()}
                                    type="button"
                                    onClick={() =>
                                        setNewHand([...newHand, d.name])
                                    }
                                    className="px-3 py-2 rounded-lg border  border-gray-200 hover:bg-gray-50"
                                >
                                    {d.name} (
                                    {
                                        newHand.filter(
                                            (c: Card) => c === d.name,
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

// ---------------- Step 3 ----------------
function Step3({ expanded, toggle, analysisProps }: any) {
    const { hands, job, loading, loadingMessage, runAnalysis } = analysisProps

    const p5 = job?.result?.value ? parseFloat(job.result.value) : null
    const p6 = job?.result?.value_6 ? parseFloat(job.result.value_6) : null

    return (
        <Panel
            title="Step 3 — Run Analysis"
            expanded={expanded}
            toggle={() => !loading && toggle()}
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
