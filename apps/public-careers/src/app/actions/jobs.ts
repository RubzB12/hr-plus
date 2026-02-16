'use server'

import { getJobFacets } from '@/lib/dal'
import type { JobFacets } from '@/types/api'

/**
 * Server Action to fetch job facets with current filter context.
 * Used by Client Components to get dynamic filter counts.
 */
export async function fetchJobFacets(params?: {
  search?: string
  department?: string
  location?: string
  employment_type?: string
  remote_policy?: string
  level?: string
}): Promise<JobFacets | null> {
  try {
    return await getJobFacets(params)
  } catch (error) {
    console.error('Failed to fetch job facets:', error)
    // Graceful degradation - return null instead of throwing
    return null
  }
}
