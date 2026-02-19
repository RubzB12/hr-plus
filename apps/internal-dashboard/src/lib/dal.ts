import 'server-only'

import { cookies } from 'next/headers'

const API_URL = process.env.DJANGO_API_URL

async function getAuthHeaders() {
  const cookieStore = await cookies()
  const sessionCookie = cookieStore.get('internal_session')

  if (!sessionCookie) {
    throw new Error('Unauthorized - No session cookie found')
  }

  return {
    'Content-Type': 'application/json',
    Cookie: `sessionid=${sessionCookie.value}`,
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

  if (!res.ok) {
    const errorText = await res.text()
    console.error('Dashboard API Error:', {
      status: res.status,
      statusText: res.statusText,
      body: errorText,
      url: `${API_URL}/api/v1/internal/analytics/dashboard/recruiter/`,
    })
    throw new Error(`Failed to fetch dashboard: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export async function getInterviews(params?: {
  status?: string
  from_date?: string
  to_date?: string
  application?: string
}) {
  const searchParams = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v != null) as [
      string,
      string,
    ][]
  )
  const res = await fetch(
    `${API_URL}/api/v1/internal/interviews/?${searchParams}`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch interviews')
  return res.json()
}

export async function getInterviewDetail(id: string) {
  const res = await fetch(`${API_URL}/api/v1/internal/interviews/${id}/`, {
    headers: await getAuthHeaders(),
    cache: 'no-store',
  })

  if (!res.ok) throw new Error('Failed to fetch interview')
  return res.json()
}

export async function getInterviewScorecards(interviewId: string) {
  const res = await fetch(
    `${API_URL}/api/v1/internal/interviews/${interviewId}/scorecards/`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) {
    if (res.status === 403) {
      // User must submit their own scorecard first
      return { restricted: true, scorecards: [] }
    }
    throw new Error('Failed to fetch scorecards')
  }
  const scorecards = await res.json()
  return { restricted: false, scorecards }
}

export async function getOffers(params?: {
  status?: string
  application?: string
  page?: string
}) {
  const searchParams = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v != null) as [
      string,
      string,
    ][]
  )
  const res = await fetch(
    `${API_URL}/api/v1/internal/offers/?${searchParams}`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch offers')
  return res.json()
}

export async function getOfferDetail(id: string) {
  const res = await fetch(`${API_URL}/api/v1/internal/offers/${id}/`, {
    headers: await getAuthHeaders(),
    cache: 'no-store',
  })

  if (!res.ok) throw new Error('Failed to fetch offer')
  return res.json()
}

export async function getJobLevels() {
  const res = await fetch(`${API_URL}/api/v1/internal/job-levels/`, {
    headers: await getAuthHeaders(),
    next: { revalidate: 600 },
  })

  if (!res.ok) throw new Error('Failed to fetch job levels')
  return res.json()
}

export async function searchCandidates(params?: {
  q?: string
  skills?: string
  location_city?: string
  location_country?: string
  experience_min?: string
  experience_max?: string
  work_authorization?: string
  source?: string
  limit?: string
}) {
  const searchParams = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v != null && v !== '') as [
      string,
      string,
    ][]
  )

  const res = await fetch(
    `${API_URL}/api/v1/internal/candidates/search/?${searchParams}`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to search candidates')
  return res.json()
}

export async function getCandidateDetail(id: string) {
  const res = await fetch(`${API_URL}/api/v1/internal/candidates/${id}/`, {
    headers: await getAuthHeaders(),
    cache: 'no-store',
  })

  if (!res.ok) throw new Error('Failed to fetch candidate')
  return res.json()
}

export async function getExecutiveDashboard(params?: {
  start_date?: string
  end_date?: string
  department_id?: string
}) {
  const searchParams = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v != null && v !== '') as [
      string,
      string,
    ][]
  )

  const res = await fetch(
    `${API_URL}/api/v1/internal/analytics/dashboard/executive/?${searchParams}`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch executive dashboard')
  return res.json()
}

export async function getTimeToFillAnalytics(params?: {
  start_date?: string
  end_date?: string
  department_id?: string
}) {
  const searchParams = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v != null && v !== '') as [
      string,
      string,
    ][]
  )

  const res = await fetch(
    `${API_URL}/api/v1/internal/analytics/time-to-fill/?${searchParams}`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch time to fill analytics')
  return res.json()
}

export async function getSourceEffectiveness(params?: {
  start_date?: string
  end_date?: string
  department_id?: string
}) {
  const searchParams = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v != null && v !== '') as [
      string,
      string,
    ][]
  )

  const res = await fetch(
    `${API_URL}/api/v1/internal/analytics/source-effectiveness/?${searchParams}`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch source effectiveness')
  return res.json()
}

export async function getInterviewerCalibration(params?: {
  start_date?: string
  end_date?: string
}) {
  const searchParams = new URLSearchParams(
    Object.entries(params ?? {}).filter(([, v]) => v != null && v !== '') as [
      string,
      string,
    ][]
  )

  const res = await fetch(
    `${API_URL}/api/v1/internal/analytics/interviewer-calibration/?${searchParams}`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch interviewer calibration')
  return res.json()
}

export async function getRequisitionCriteria(requisitionId: string) {
  const res = await fetch(
    `${API_URL}/api/v1/internal/requisitions/${requisitionId}/criteria/`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to fetch requisition criteria')
  return res.json()
}

export async function rescoreApplication(applicationId: string) {
  const res = await fetch(
    `${API_URL}/api/v1/internal/applications/${applicationId}/rescore/`,
    {
      method: 'POST',
      headers: await getAuthHeaders(),
      cache: 'no-store',
    }
  )

  if (!res.ok) throw new Error('Failed to trigger rescore')
  return res.json()
}
