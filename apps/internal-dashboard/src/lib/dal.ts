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

export async function getMe() {
  const res = await fetch(`${API_URL}/api/v1/auth/me/`, {
    headers: await getAuthHeaders(),
    cache: 'no-store',
  })

  if (!res.ok) throw new Error('Failed to fetch user')
  return res.json()
}

export async function getDepartments() {
  const res = await fetch(`${API_URL}/api/v1/internal/departments/`, {
    headers: await getAuthHeaders(),
    cache: 'no-store',
  })

  if (!res.ok) throw new Error('Failed to fetch departments')
  return res.json()
}

export async function getInternalUsers(params?: {
  department?: string
  role?: string
  page?: string
}) {
  const searchParams = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v != null) as [
      string,
      string,
    ][]
  )
  const res = await fetch(
    `${API_URL}/api/v1/internal/users/?${searchParams}`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch users')
  return res.json()
}

export async function getLocations() {
  const res = await fetch(`${API_URL}/api/v1/internal/locations/`, {
    headers: await getAuthHeaders(),
    next: { revalidate: 600 },
  })

  if (!res.ok) throw new Error('Failed to fetch locations')
  return res.json()
}

export async function getRequisitions(params?: {
  status?: string
  department?: string
  recruiter?: string
  page?: string
}) {
  const searchParams = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v != null) as [
      string,
      string,
    ][]
  )
  const res = await fetch(
    `${API_URL}/api/v1/internal/requisitions/?${searchParams}`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch requisitions')
  return res.json()
}

export async function getRequisitionDetail(id: string) {
  const res = await fetch(
    `${API_URL}/api/v1/internal/requisitions/${id}/`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch requisition')
  return res.json()
}

export async function getPipelineBoard(requisitionId: string) {
  const res = await fetch(
    `${API_URL}/api/v1/internal/requisitions/${requisitionId}/pipeline/`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch pipeline')
  return res.json()
}

export async function getApplications(params?: {
  status?: string
  stage?: string
  search?: string
  page?: string
}) {
  const searchParams = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v != null) as [
      string,
      string,
    ][]
  )
  const res = await fetch(
    `${API_URL}/api/v1/internal/applications/?${searchParams}`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch applications')
  return res.json()
}

export async function getApplicationDetail(id: string) {
  const res = await fetch(
    `${API_URL}/api/v1/internal/applications/${id}/`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch application')
  return res.json()
}

export async function getPendingApprovals() {
  const res = await fetch(
    `${API_URL}/api/v1/internal/pending-approvals/`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch pending approvals')
  return res.json()
}

export async function getRecruiterDashboard() {
  const res = await fetch(
    `${API_URL}/api/v1/internal/analytics/dashboard/recruiter/`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch dashboard')
  return res.json()
}
