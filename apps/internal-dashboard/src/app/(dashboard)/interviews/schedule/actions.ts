'use server'

import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'

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

export async function scheduleInterview(formData: FormData) {
  try {
    const headers = await getAuthHeaders()

    const data = {
      application_id: formData.get('application_id'),
      type: formData.get('type'),
      scheduled_start: formData.get('scheduled_start'),
      scheduled_end: formData.get('scheduled_end'),
      timezone: formData.get('timezone') || 'UTC',
      location: formData.get('location') || '',
      video_link: formData.get('video_link') || '',
      prep_notes_interviewer: formData.get('prep_notes_interviewer') || '',
      prep_notes_candidate: formData.get('prep_notes_candidate') || '',
      interviewer_ids: formData.get('interviewer_ids')
        ? JSON.parse(formData.get('interviewer_ids') as string)
        : [],
    }

    const response = await fetch(
      `${API_URL}/api/v1/internal/interviews/`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      }
    )

    if (!response.ok) {
      const error = await response.json()
      return {
        success: false,
        error: error.detail || JSON.stringify(error) || 'Failed to schedule interview'
      }
    }

    const interview = await response.json()

    // Revalidate interviews page
    revalidatePath('/interviews')

    return {
      success: true,
      interviewId: interview.id
    }
  } catch (error: any) {
    console.error('Schedule interview error:', error)
    return {
      success: false,
      error: error.message || 'Failed to schedule interview'
    }
  }
}
