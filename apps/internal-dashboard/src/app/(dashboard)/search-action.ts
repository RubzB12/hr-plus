'use server'

import { getApplications, searchCandidates } from '@/lib/dal'

interface SearchResult {
  applications: Array<{
    id: string
    candidate_name: string
    requisition_title: string
    status: string
  }>
  candidates: Array<{
    id: string
    candidate_name: string
    candidate_email: string
  }>
}

export async function globalSearch(query: string): Promise<SearchResult> {
  if (!query || query.trim().length < 2) {
    return { applications: [], candidates: [] }
  }

  const [applicationsResult, candidatesResult] = await Promise.allSettled([
    getApplications({ search: query }),
    searchCandidates({ q: query, limit: '5' }),
  ])

  const applications =
    applicationsResult.status === 'fulfilled'
      ? (applicationsResult.value?.results ?? []).slice(0, 5).map((a: any) => ({
          id: a.id,
          candidate_name: a.candidate_name,
          requisition_title: a.requisition_title,
          status: a.status,
        }))
      : []

  const candidates =
    candidatesResult.status === 'fulfilled'
      ? (candidatesResult.value?.results ?? []).slice(0, 5).map((c: any) => ({
          id: c.id,
          candidate_name: `${c.user?.first_name ?? ''} ${c.user?.last_name ?? ''}`.trim() || c.candidate_name || 'Unknown',
          candidate_email: c.user?.email ?? c.candidate_email ?? '',
        }))
      : []

  return { applications, candidates }
}
