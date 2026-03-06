import { useState, useRef, useEffect } from 'react'
import { createJob, getJob } from './services/consistency'
import type { ConsistencyJobResponse } from './services/consistency'
import './App.css'

type CardEntry = { count: number; name: string }

function App() {
    const [deckInput, setDeckInput] = useState<string>('')
    const [cards, setCards] = useState<CardEntry[]>([])
    const [selectedCards, setSelectedCards] = useState<Set<string>>(new Set())
    const [idealHands, setIdealHands] = useState<Set<string>[]>([])
    const [job, setJob] = useState<ConsistencyJobResponse | null>(null)
    const [loading, setLoading] = useState<boolean>(false)
    const [error, setError] = useState<string | null>(null)
    const pollInterval = useRef<number | null>(null)

    // Parse deck text input into cards
    const parseDeck = () => {
        const lines = deckInput
            .split('\n')
            .map((line) => line.trim())
            .filter(Boolean)
        const parsed: CardEntry[] = []

        for (const line of lines) {
            const match = line.match(/^(\d+)\s+(.+)$/)
            if (!match) {
                setError(`Invalid line format: "${line}"`)
                return
            }
            parsed.push({ count: parseInt(match[1], 10), name: match[2] })
        }

        setCards(parsed)
        setSelectedCards(new Set())
        setIdealHands([])
        setError(null)
    }

    // Toggle card selection for current ideal hand
    const toggleCardSelection = (name: string) => {
        setSelectedCards((prev) => {
            const copy = new Set(prev)
            if (copy.has(name)) copy.delete(name)
            else copy.add(name)
            return copy
        })
    }

    // Add current selection as an ideal hand
    const addIdealHand = () => {
        if (selectedCards.size === 0) return
        setIdealHands((prev) => [...prev, new Set(selectedCards)])
        setSelectedCards(new Set())
    }

    // Submit payload and start polling
    const handleSubmit = () => {
        if (!cards.length || idealHands.length === 0) {
            setError('Deck not parsed or no ideal hands added')
            return
        }

        const names = cards.map((c) => c.name)
        const ratios = cards.map((c) => c.count)
        const hands = idealHands.map((s) => Array.from(s))

        const payload = {
            deckcount: cards.reduce((sum, c) => sum + c.count, 0),
            names,
            ratios,
            ideal_hands: hands,
            num_hands: 100000,
        }

        setLoading(true)
        setError(null)
        setJob(null)

        createJob(payload)
            .then((job) => {
                setJob(job)
                startPolling(job.jobId)
            })
            .catch((e: any) => {
                setError(e?.response?.data || e?.message || 'Unknown error')
                setLoading(false)
            })
    }

    // Poll job status until result is available
    const startPolling = (jobId: string) => {
        pollInterval.current = window.setInterval(() => {
            getJob(jobId)
                .then((data) => {
                    setJob(data)
                    if (data.result && pollInterval.current) {
                        clearInterval(pollInterval.current)
                        pollInterval.current = null
                        setLoading(false)
                    }
                })
                .catch((e: any) => {
                    setError(e?.response?.data || e?.message || 'Unknown error')
                    setLoading(false)
                    if (pollInterval.current) {
                        clearInterval(pollInterval.current)
                        pollInterval.current = null
                    }
                })
        }, 5000)
    }

    // Clear polling on unmount
    useEffect(() => {
        return () => {
            if (pollInterval.current) clearInterval(pollInterval.current)
        }
    }, [])

    return (
        <div className="App">
            <h1>Consistency Job Runner</h1>

            <h2>Paste your deck list</h2>
            <textarea
                rows={15}
                cols={60}
                value={deckInput}
                onChange={(e) => setDeckInput(e.target.value)}
            />
            <br />
            <button onClick={parseDeck}>Parse Deck</button>

            {error && <p style={{ color: 'red' }}>{error}</p>}

            {cards.length > 0 && (
                <div>
                    <h2>Select cards for current ideal hand</h2>
                    <ul style={{ listStyle: 'none', padding: 0 }}>
                        {cards.map((card) => (
                            <li key={card.name}>
                                <label>
                                    <input
                                        type="checkbox"
                                        checked={selectedCards.has(card.name)}
                                        onChange={() =>
                                            toggleCardSelection(card.name)
                                        }
                                    />
                                    {card.count} × {card.name}
                                </label>
                            </li>
                        ))}
                    </ul>
                    <button
                        onClick={addIdealHand}
                        disabled={selectedCards.size === 0}
                    >
                        Add Ideal Hand
                    </button>

                    {idealHands.length > 0 && (
                        <div>
                            <h3>Current Ideal Hands</h3>
                            <ul>
                                {idealHands.map((hand, i) => (
                                    <li key={i}>
                                        {Array.from(hand).join(', ')}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <button
                        onClick={handleSubmit}
                        disabled={loading || idealHands.length === 0}
                    >
                        {loading ? 'Processing...' : 'Run Test Hands'}
                    </button>
                </div>
            )}

            {job && job.result && (
                <div>
                    <h2>Job Result</h2>
                    <pre>{JSON.stringify(job.result, null, 2)}</pre>
                </div>
            )}

            {job && !job.result && !loading && (
                <p>Job status: {job.status}. Waiting for result...</p>
            )}
        </div>
    )
}

export default App
