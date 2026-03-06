import { useState, useEffect, useRef } from 'react'
import { z } from 'zod'
import './App.css'

const ConsistencyJobSchema = z.object({
    jobId: z.string(),
    status: z.string(),
    result: z.object({}).optional().nullable(),
})

type ConsistencyJobResponse = z.infer<typeof ConsistencyJobSchema>

function App() {
    const [jsonInput, setJsonInput] = useState<string>('{}')
    const [job, setJob] = useState<ConsistencyJobResponse | null>(null)
    const [loading, setLoading] = useState<boolean>(false)
    const [error, setError] = useState<string | null>(null)
    const pollInterval = useRef<number | null>(null)

    const API_URL = import.meta.env.VITE_API_URL || ''

    const handleSubmit = async () => {
        setError(null)
        setJob(null)
        setLoading(true)

        let payload
        try {
            payload = JSON.parse(jsonInput)
        } catch (e) {
            setError('Invalid JSON')
            setLoading(false)
            return
        }

        try {
            const response = await fetch(`${API_URL}/consistency/jobs/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })
            if (!response.ok) {
                const text = await response.text()
                throw new Error(`Server error: ${text}`)
            }

            const dataRaw = await response.json()
            const data = ConsistencyJobSchema.parse(dataRaw) // Zod validation
            setJob(data)
            pollJobStatus(data.jobId)
        } catch (e: any) {
            setError(e?.message || 'Unknown error')
            setLoading(false)
        }
    }

    const pollJobStatus = (job_id: string) => {
        pollInterval.current = window.setInterval(async () => {
            try {
                const response = await fetch(
                    `${API_URL}/consistency/jobs/${job_id}`
                )
                if (!response.ok) throw new Error('Failed to fetch job status')

                const dataRaw = await response.json()
                const data = ConsistencyJobSchema.parse(dataRaw)
                setJob(data)

                if (data.result) {
                    setLoading(false)
                    if (pollInterval.current) {
                        clearInterval(pollInterval.current)
                        pollInterval.current = null
                    }
                }
            } catch (e: any) {
                setError(e?.message || 'Unknown error')
                setLoading(false)
                if (pollInterval.current) {
                    clearInterval(pollInterval.current)
                    pollInterval.current = null
                }
            }
        }, 5000)
    }

    useEffect(() => {
        return () => {
            if (pollInterval.current) clearInterval(pollInterval.current)
        }
    }, [])

    return (
        <div className="App">
            <h1>Consistency Job Runner</h1>
            <textarea
                rows={10}
                cols={50}
                value={jsonInput}
                onChange={(e) => setJsonInput(e.target.value)}
            />
            <br />
            <button onClick={handleSubmit} disabled={loading}>
                {loading ? 'Processing...' : 'Submit'}
            </button>

            {loading && <p>⏳ Job is processing...</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}
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
