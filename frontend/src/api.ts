import type { Job } from './types'

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init)
  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.message || error?.detail?.message ||
      (typeof error?.detail === 'string' ? error.detail : `Request failed (${response.status})`))
  }
  return response.json() as Promise<T>
}
export function post<T>(path: string, body: unknown) {
  return request<T>(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
}
export async function waitJob<T>(id: string, progress?: (job: Job<T>) => void): Promise<T> {
  const started = Date.now()
  while (Date.now() - started < 600000) {
    const job = await request<Job<T>>(`/jobs/${id}`)
    progress?.(job)
    if (job.state === 'succeeded') {
      if (!job.result) throw new Error('Worker returned no result')
      return job.result
    }
    if (['failed', 'interrupted'].includes(job.state)) throw new Error(job.error || 'Analysis was interrupted. Retry when the worker is available.')
    await new Promise(resolve => setTimeout(resolve, 600))
  }
  throw new Error('Worker did not finish. Your existing results have been preserved.')
}
