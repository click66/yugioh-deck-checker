import axios from 'axios'
import { z } from 'zod'

export const JobStatus = {
    FAILED: 'failed',
    PENDING: 'pending',
    RUNNING: 'running',
    COMPLETED: 'completed',
} as const

export type JobStatusType = (typeof JobStatus)[keyof typeof JobStatus]

export const ConsistencyJobErrorSchema = z.object({
    code: z.string(),
    detail: z.string(),
})

export const ConsistencyJobSchema = z.object({
    jobId: z.string(),
    status: z.enum([
        JobStatus.PENDING,
        JobStatus.RUNNING,
        JobStatus.COMPLETED,
        JobStatus.FAILED,
    ]),
    result: z
        .object({
            value: z.string(),
            value_6: z.string(),
        })
        .optional()
        .nullable(),
    error: ConsistencyJobErrorSchema.optional().nullable(),
})
export type ConsistencyJobResponse = z.infer<typeof ConsistencyJobSchema>

const API_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json' },
    timeout: 10000,
})

export function createJob(payload: {
    deckcount: number
    names: string[]
    ratios: number[]
    ideal_hands: string[][]
    num_hands: number
    use_wildcards: boolean
}): Promise<ConsistencyJobResponse> {
    return api
        .post('/consistency/jobs/create', payload)
        .then((res) => ConsistencyJobSchema.parse(res.data))
}

export function getJob(jobId: string): Promise<ConsistencyJobResponse | null> {
    return api
        .get(`/consistency/jobs/${jobId}`)
        .then((res) => ConsistencyJobSchema.parse(res.data))
        .catch((err) => {
            if (err.response?.status === 404) {
                return null
            }
            throw err
        })
}
