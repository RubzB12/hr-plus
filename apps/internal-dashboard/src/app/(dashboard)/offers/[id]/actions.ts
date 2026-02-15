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

export async function submitForApproval(offerId: string, approverIds: string[]) {
  try {
    const headers = await getAuthHeaders()

    const response = await fetch(
      `${API_URL}/api/v1/internal/offers/${offerId}/submit_for_approval/`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({ approvers: approverIds }),
      }
    )

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to submit for approval' }
    }

    revalidatePath(`/offers/${offerId}`)
    revalidatePath('/offers')

    return { success: true }
  } catch (error: any) {
    console.error('Submit for approval error:', error)
    return { success: false, error: error.message || 'Failed to submit for approval' }
  }
}

export async function sendToCandidate(offerId: string) {
  try {
    const headers = await getAuthHeaders()

    const response = await fetch(
      `${API_URL}/api/v1/internal/offers/${offerId}/send_to_candidate/`,
      {
        method: 'POST',
        headers,
      }
    )

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to send offer' }
    }

    revalidatePath(`/offers/${offerId}`)
    revalidatePath('/offers')

    return { success: true }
  } catch (error: any) {
    console.error('Send offer error:', error)
    return { success: false, error: error.message || 'Failed to send offer' }
  }
}

export async function withdrawOffer(offerId: string) {
  try {
    const headers = await getAuthHeaders()

    const response = await fetch(
      `${API_URL}/api/v1/internal/offers/${offerId}/withdraw/`,
      {
        method: 'POST',
        headers,
      }
    )

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to withdraw offer' }
    }

    revalidatePath(`/offers/${offerId}`)
    revalidatePath('/offers')

    return { success: true }
  } catch (error: any) {
    console.error('Withdraw offer error:', error)
    return { success: false, error: error.message || 'Failed to withdraw offer' }
  }
}

export async function approveOffer(approvalId: string, comments: string) {
  try {
    const headers = await getAuthHeaders()

    const response = await fetch(
      `${API_URL}/api/v1/internal/offer-approvals/${approvalId}/approve/`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({ comments }),
      }
    )

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to approve' }
    }

    const approval = await response.json()

    revalidatePath(`/offers/${approval.offer}`)
    revalidatePath('/offers')

    return { success: true }
  } catch (error: any) {
    console.error('Approve error:', error)
    return { success: false, error: error.message || 'Failed to approve' }
  }
}

export async function rejectOffer(approvalId: string, comments: string) {
  try {
    const headers = await getAuthHeaders()

    const response = await fetch(
      `${API_URL}/api/v1/internal/offer-approvals/${approvalId}/reject/`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({ comments }),
      }
    )

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || 'Failed to reject' }
    }

    const approval = await response.json()

    revalidatePath(`/offers/${approval.offer}`)
    revalidatePath('/offers')

    return { success: true }
  } catch (error: any) {
    console.error('Reject error:', error)
    return { success: false, error: error.message || 'Failed to reject' }
  }
}
