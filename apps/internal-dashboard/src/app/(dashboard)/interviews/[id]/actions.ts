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

export async function submitScorecard(interviewId: string, formData: FormData) {
  try {
    const headers = await getAuthHeaders()

    const data = {
      overall_rating: formData.get('overall_rating')
        ? parseInt(formData.get('overall_rating') as string)
        : null,
      recommendation: formData.get('recommendation') || null,
      strengths: formData.get('strengths') || '',
      concerns: formData.get('concerns') || '',
      notes: formData.get('notes') || '',
      is_draft: formData.get('is_draft') === 'true',
    }

    const response = await fetch(
      `${API_URL}/api/v1/internal/interviews/${interviewId}/scorecards/`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      }
    )

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to submit scorecard' }
    }

    const scorecard = await response.json()

    revalidatePath(`/interviews/${interviewId}`)
    revalidatePath('/interviews')

    return { success: true, scorecardId: scorecard.id }
  } catch (error: any) {
    console.error('Scorecard submission error:', error)
    return { success: false, error: error.message || 'Failed to submit scorecard' }
  }
}

export async function cancelInterview(interviewId: string, reason: string) {
  try {
    const headers = await getAuthHeaders()

    const response = await fetch(
      `${API_URL}/api/v1/internal/interviews/${interviewId}/cancel/`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({ reason }),
      }
    )

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to cancel interview' }
    }

    revalidatePath(`/interviews/${interviewId}`)
    revalidatePath('/interviews')

    return { success: true }
  } catch (error: any) {
    console.error('Cancel interview error:', error)
    return { success: false, error: error.message || 'Failed to cancel interview' }
  }
}

export async function completeInterview(interviewId: string) {
  try {
    const headers = await getAuthHeaders()

    const response = await fetch(
      `${API_URL}/api/v1/internal/interviews/${interviewId}/complete/`,
      {
        method: 'POST',
        headers,
      }
    )

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to mark interview complete' }
    }

    revalidatePath(`/interviews/${interviewId}`)
    revalidatePath('/interviews')

    return { success: true }
  } catch (error: any) {
    console.error('Complete interview error:', error)
    return { success: false, error: error.message || 'Failed to mark interview complete' }
  }
}
