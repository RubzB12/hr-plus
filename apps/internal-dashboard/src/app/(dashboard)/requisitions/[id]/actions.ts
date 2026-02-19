'use server'

import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'

const API_URL = process.env.DJANGO_API_URL

async function performAction(
  id: string,
  actionPath: string,
): Promise<{ success: boolean; error?: string }> {
  const cookieStore = await cookies()
  const sessionCookie = cookieStore.get('internal_session')
  if (!sessionCookie) {
    return { success: false, error: 'Unauthorized' }
  }

  const res = await fetch(
    `${API_URL}/api/v1/internal/requisitions/${id}/${actionPath}/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${sessionCookie.value}`,
      },
    },
  )

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    return { success: false, error: data.detail ?? 'Action failed' }
  }

  revalidatePath('/requisitions')
  revalidatePath(`/requisitions/${id}`)
  return { success: true }
}

export async function requisitionPublishAction(id: string) {
  return performAction(id, 'publish')
}

export async function requisitionHoldAction(id: string) {
  return performAction(id, 'hold')
}

export async function requisitionCancelAction(id: string) {
  return performAction(id, 'cancel')
}

export async function requisitionReopenAction(id: string) {
  return performAction(id, 'reopen')
}

export async function requisitionCloneAction(id: string) {
  return performAction(id, 'clone')
}
