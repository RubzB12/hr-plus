import 'server-only'

import { cookies } from 'next/headers'

const API_URL = process.env.DJANGO_API_URL

async function getAuthHeaders() {
  const cookieStore = await cookies()
  const sessionCookie = cookieStore.get('session')
  if (!sessionCookie) {
    throw new Error('Unauthorized')
  }

  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${sessionCookie.value}`,
  }
}

export async function getJobs(params?: {
  department?: string
  location?: string
  search?: string
  employment_type?: string
  remote_policy?: string
  page?: string
}) {
  const searchParams = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v != null) as [
      string,
      string,
    ][]
  )
  const res = await fetch(`${API_URL}/api/v1/jobs/?${searchParams}`, {
    headers: { 'Content-Type': 'application/json' },
    next: { revalidate: 300 },
  })

  if (!res.ok) throw new Error('Failed to fetch jobs')
  return res.json()
}

export async function getJobBySlug(slug: string) {
  const res = await fetch(`${API_URL}/api/v1/jobs/${slug}/`, {
    headers: { 'Content-Type': 'application/json' },
    next: { revalidate: 300 },
  })

  if (!res.ok) throw new Error('Failed to fetch job')
  return res.json()
}

export async function getSimilarJobs(jobId: string) {
  const res = await fetch(`${API_URL}/api/v1/jobs/${jobId}/similar/`, {
    headers: { 'Content-Type': 'application/json' },
    next: { revalidate: 300 },
  })

  if (!res.ok) throw new Error('Failed to fetch similar jobs')
  return res.json()
}

export async function getCategories() {
  const res = await fetch(`${API_URL}/api/v1/jobs/categories/`, {
    headers: { 'Content-Type': 'application/json' },
    next: { revalidate: false },
  })

  if (!res.ok) throw new Error('Failed to fetch categories')
  return res.json()
}

export async function getLocations() {
  const res = await fetch(`${API_URL}/api/v1/locations/`, {
    headers: { 'Content-Type': 'application/json' },
    next: { revalidate: false },
  })

  if (!res.ok) throw new Error('Failed to fetch locations')
  return res.json()
}

export async function getJobFacets(params?: {
  search?: string
  department?: string
  location?: string
  employment_type?: string
  remote_policy?: string
  level?: string
}) {
  const searchParams = new URLSearchParams(params as any)
  const res = await fetch(`${API_URL}/api/v1/jobs/facets/?${searchParams}`, {
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store', // Always get fresh counts
  })

  if (!res.ok) throw new Error('Failed to fetch job facets')
  return res.json()
}

export async function getProfile() {
  const res = await fetch(`${API_URL}/api/v1/candidates/profile/`, {
    headers: await getAuthHeaders(),
    cache: 'no-store',
  })

  if (!res.ok) throw new Error('Failed to fetch profile')
  return res.json()
}

export async function getRecommendations(limit: number = 10) {
  const res = await fetch(`${API_URL}/api/v1/candidates/recommendations/?limit=${limit}`, {
    headers: await getAuthHeaders(),
    cache: 'no-store', // Always get fresh recommendations
  })

  if (!res.ok) throw new Error('Failed to fetch recommendations')
  return res.json()
}

export async function getApplications() {
  const res = await fetch(`${API_URL}/api/v1/applications/`, {
    headers: await getAuthHeaders(),
    cache: 'no-store',
  })

  if (!res.ok) throw new Error('Failed to fetch applications')
  return res.json()
}

export async function getApplicationDetail(id: string) {
  const res = await fetch(`${API_URL}/api/v1/applications/${id}/`, {
    headers: await getAuthHeaders(),
    cache: 'no-store',
  })

  if (!res.ok) throw new Error('Failed to fetch application')
  return res.json()
}

export async function getMe() {
  const res = await fetch(`${API_URL}/api/v1/auth/me/`, {
    headers: await getAuthHeaders(),
    cache: 'no-store',
  })

  if (!res.ok) return null
  return res.json()
}

export async function updateProfile(data: Record<string, unknown>) {
  const res = await fetch(`${API_URL}/api/v1/candidates/profile/`, {
    method: 'PUT',
    headers: await getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const error = await res.json()
    throw new Error(JSON.stringify(error))
  }
  return res.json()
}

export async function createApplication(data: {
  requisition_id: string
  cover_letter?: string
  screening_responses?: Record<string, string>
  source?: string
}) {
  const res = await fetch(`${API_URL}/api/v1/applications/apply/`, {
    method: 'POST',
    headers: await getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const error = await res.json()
    throw new Error(JSON.stringify(error))
  }
  return res.json()
}

export async function withdrawApplication(id: string) {
  const res = await fetch(`${API_URL}/api/v1/applications/${id}/withdraw/`, {
    method: 'POST',
    headers: await getAuthHeaders(),
  })
  if (!res.ok) {
    const error = await res.json()
    throw new Error(JSON.stringify(error))
  }
  return res.json()
}

export async function getSavedSearches() {
  const res = await fetch(`${API_URL}/api/v1/candidates/saved-searches/`, {
    headers: await getAuthHeaders(),
    cache: 'no-store',
  })
  if (!res.ok) throw new Error('Failed to fetch saved searches')
  return res.json()
}

export async function getSavedSearch(id: string) {
  const res = await fetch(`${API_URL}/api/v1/candidates/saved-searches/${id}/`, {
    headers: await getAuthHeaders(),
    cache: 'no-store',
  })
  if (!res.ok) throw new Error('Failed to fetch saved search')
  return res.json()
}

export async function createSavedSearch(data: {
  name: string
  search_params: Record<string, any>
  alert_frequency: string
}) {
  const res = await fetch(`${API_URL}/api/v1/candidates/saved-searches/`, {
    method: 'POST',
    headers: await getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const error = await res.json()
    throw new Error(JSON.stringify(error))
  }
  return res.json()
}

export async function updateSavedSearch(id: string, data: Partial<{
  name: string
  search_params: Record<string, any>
  alert_frequency: string
  is_active: boolean
}>) {
  const res = await fetch(`${API_URL}/api/v1/candidates/saved-searches/${id}/`, {
    method: 'PUT',
    headers: await getAuthHeaders(),
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const error = await res.json()
    throw new Error(JSON.stringify(error))
  }
  return res.json()
}

export async function deleteSavedSearch(id: string) {
  const res = await fetch(`${API_URL}/api/v1/candidates/saved-searches/${id}/`, {
    method: 'DELETE',
    headers: await getAuthHeaders(),
  })
  if (!res.ok) throw new Error('Failed to delete saved search')
}

export async function getSavedSearchMatches(id: string) {
  const res = await fetch(`${API_URL}/api/v1/candidates/saved-searches/${id}/matches/`, {
    headers: await getAuthHeaders(),
    cache: 'no-store',
  })
  if (!res.ok) throw new Error('Failed to fetch matches')
  return res.json()
}

export async function toggleSavedSearchAlerts(id: string) {
  const res = await fetch(`${API_URL}/api/v1/candidates/saved-searches/${id}/toggle-alerts/`, {
    method: 'POST',
    headers: await getAuthHeaders(),
  })
  if (!res.ok) throw new Error('Failed to toggle alerts')
  return res.json()
}

export async function getJobAlerts() {
  const res = await fetch(`${API_URL}/api/v1/candidates/job-alerts/`, {
    headers: await getAuthHeaders(),
    cache: 'no-store',
  })
  if (!res.ok) throw new Error('Failed to fetch job alerts')
  return res.json()
}
