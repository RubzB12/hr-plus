'use server'

import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'

const API_URL = process.env.DJANGO_API_URL

async function getHeaders(): Promise<
  { headers: HeadersInit } | { error: string }
> {
  const cookieStore = await cookies()
  const sessionCookie = cookieStore.get('internal_session')
  if (!sessionCookie) {
    return { error: 'Unauthorized' }
  }
  return {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${sessionCookie.value}`,
    },
  }
}

export async function moveToStage(
  applicationId: string,
  stageId: string,
): Promise<{ success: boolean; error?: string }> {
  const auth = await getHeaders()
  if ('error' in auth) return { success: false, error: auth.error }

  const res = await fetch(
    `${API_URL}/api/v1/internal/applications/${applicationId}/move-stage/`,
    {
      method: 'POST',
      ...auth,
      body: JSON.stringify({ stage_id: stageId }),
    },
  )

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    return { success: false, error: data.detail ?? 'Failed to move stage' }
  }

  revalidatePath('/applications')
  revalidatePath(`/applications/${applicationId}`)
  return { success: true }
}

export async function rejectApplication(
  applicationId: string,
  reason: string,
): Promise<{ success: boolean; error?: string }> {
  const auth = await getHeaders()
  if ('error' in auth) return { success: false, error: auth.error }

  const res = await fetch(
    `${API_URL}/api/v1/internal/applications/${applicationId}/reject/`,
    {
      method: 'POST',
      ...auth,
      body: JSON.stringify({ reason }),
    },
  )

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    return { success: false, error: data.detail ?? 'Failed to reject' }
  }

  revalidatePath('/applications')
  revalidatePath(`/applications/${applicationId}`)
  return { success: true }
}

export async function toggleStar(
  applicationId: string,
): Promise<{ success: boolean; error?: string }> {
  const auth = await getHeaders()
  if ('error' in auth) return { success: false, error: auth.error }

  const res = await fetch(
    `${API_URL}/api/v1/internal/applications/${applicationId}/star/`,
    {
      method: 'POST',
      ...auth,
    },
  )

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    return { success: false, error: data.detail ?? 'Failed to toggle star' }
  }

  revalidatePath('/applications')
  revalidatePath(`/applications/${applicationId}`)
  return { success: true }
}

export async function addNote(
  applicationId: string,
  body: string,
  isPrivate: boolean = false,
): Promise<{ success: boolean; error?: string }> {
  const auth = await getHeaders()
  if ('error' in auth) return { success: false, error: auth.error }

  const res = await fetch(
    `${API_URL}/api/v1/internal/applications/${applicationId}/notes/`,
    {
      method: 'POST',
      ...auth,
      body: JSON.stringify({ body, is_private: isPrivate }),
    },
  )

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    return { success: false, error: data.detail ?? 'Failed to add note' }
  }

  revalidatePath(`/applications/${applicationId}`)
  return { success: true }
}

export async function addTag(
  applicationId: string,
  tagName: string,
): Promise<{ success: boolean; error?: string }> {
  const auth = await getHeaders()
  if ('error' in auth) return { success: false, error: auth.error }

  const res = await fetch(
    `${API_URL}/api/v1/internal/applications/${applicationId}/add-tag/`,
    {
      method: 'POST',
      ...auth,
      body: JSON.stringify({ tag_name: tagName }),
    },
  )

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    return { success: false, error: data.detail ?? 'Failed to add tag' }
  }

  revalidatePath(`/applications/${applicationId}`)
  return { success: true }
}

export async function removeTag(
  applicationId: string,
  tagName: string,
): Promise<{ success: boolean; error?: string }> {
  const auth = await getHeaders()
  if ('error' in auth) return { success: false, error: auth.error }

  const res = await fetch(
    `${API_URL}/api/v1/internal/applications/${applicationId}/remove-tag/`,
    {
      method: 'POST',
      ...auth,
      body: JSON.stringify({ tag_name: tagName }),
    },
  )

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    return { success: false, error: data.detail ?? 'Failed to remove tag' }
  }

  revalidatePath(`/applications/${applicationId}`)
  return { success: true }
}

export async function rescoreApplicationAction(
  applicationId: string,
): Promise<{ success: boolean; error?: string }> {
  const auth = await getHeaders()
  if ('error' in auth) return { success: false, error: auth.error }

  const res = await fetch(
    `${API_URL}/api/v1/internal/applications/${applicationId}/rescore/`,
    {
      method: 'POST',
      ...auth,
    },
  )

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    return { success: false, error: data.detail ?? 'Failed to rescore' }
  }

  revalidatePath(`/applications/${applicationId}`)
  return { success: true }
}
