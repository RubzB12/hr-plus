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

export async function createOffer(formData: FormData) {
  try {
    const headers = await getAuthHeaders()

    const data = {
      application: formData.get('application'),
      title: formData.get('title'),
      level: formData.get('level'),
      department: formData.get('department'),
      reporting_to: formData.get('reporting_to') || null,
      base_salary_input: formData.get('base_salary'),
      salary_currency: formData.get('salary_currency') || 'USD',
      salary_frequency: formData.get('salary_frequency') || 'annual',
      bonus_input: formData.get('bonus') || null,
      equity: formData.get('equity') || '',
      sign_on_bonus_input: formData.get('sign_on_bonus') || null,
      relocation_input: formData.get('relocation') || null,
      start_date: formData.get('start_date'),
      expiration_date: formData.get('expiration_date'),
      notes: formData.get('notes') || '',
    }

    const response = await fetch(`${API_URL}/api/v1/internal/offers/`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.detail || JSON.stringify(error) }
    }

    const offer = await response.json()

    revalidatePath('/offers')

    return { success: true, offerId: offer.id }
  } catch (error: any) {
    console.error('Create offer error:', error)
    return { success: false, error: error.message || 'Failed to create offer' }
  }
}
