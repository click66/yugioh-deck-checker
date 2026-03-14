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
            p5: z.string(),
            p6: z.string(),
            p5_with_gambling: z.string().optional(),
            p6_with_gambling: z.string().optional(),
            rescued_5: z.string().optional(),
            rescued_6: z.string().optional(),
            gamble_seen_5: z.record(z.string(), z.string()).optional(),
            gamble_seen_6: z.record(z.string(), z.string()).optional(),
            gamble_failed_5: z.string().optional(),
            gamble_failed_6: z.string().optional(),
            gamble_unplayable_5: z.string().optional(),
            gamble_unplayable_6: z.string().optional(),
            gamble_attempted_5: z.string().optional(),
            gamble_attempted_6: z.string().optional(),
            useful_gambles_5: z.record(z.string(), z.string()).optional(),
            useful_gambles_6: z.record(z.string(), z.string()).optional(),
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
    use_gambling: boolean
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
