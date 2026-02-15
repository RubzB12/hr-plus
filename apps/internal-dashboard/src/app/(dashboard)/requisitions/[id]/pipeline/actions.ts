'use server'

import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'

const API_URL = process.env.DJANGO_API_URL

async function getAuthHeaders() {
  const cookieStore = await cookies()
  const sessionCookie = cookieStore.get('sessionid')
  if (!sessionCookie) {
    throw new Error('Unauthorized')
  }

  return {
    'Content-Type': 'application/json',
    Cookie: `sessionid=${sessionCookie.value}`,
  }
}

export async function moveApplicationToStage(
  applicationId: string,
  stageId: string,
  requisitionId: string
) {
  try {
    const headers = await getAuthHeaders()

    const response = await fetch(
      `${API_URL}/api/v1/internal/applications/${applicationId}/move_to_stage/`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({ stage_id: stageId }),
      }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to move application')
    }

    // Revalidate the pipeline page
    revalidatePath(`/requisitions/${requisitionId}/pipeline`)

    return { success: true }
  } catch (error: any) {
    console.error('Move to stage error:', error)
    return { success: false, error: error.message }
  }
}
