'use server'

import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'

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

// Work Experience Actions

export async function createExperience(data: any) {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/api/v1/candidates/experiences/`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to create experience')
    }

    revalidatePath('/dashboard/profile')
    return await response.json()
  } catch (error: any) {
    throw new Error(error.message || 'Failed to create experience')
  }
}

export async function updateExperience(id: string, data: any) {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/api/v1/candidates/experiences/${id}/`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to update experience')
    }

    revalidatePath('/dashboard/profile')
    return await response.json()
  } catch (error: any) {
    throw new Error(error.message || 'Failed to update experience')
  }
}

export async function deleteExperience(id: string) {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/api/v1/candidates/experiences/${id}/`, {
      method: 'DELETE',
      headers,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to delete experience')
    }

    revalidatePath('/dashboard/profile')
    return { success: true }
  } catch (error: any) {
    throw new Error(error.message || 'Failed to delete experience')
  }
}

// Education Actions

export async function createEducation(data: any) {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/api/v1/candidates/education/`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to create education')
    }

    revalidatePath('/dashboard/profile')
    return await response.json()
  } catch (error: any) {
    throw new Error(error.message || 'Failed to create education')
  }
}

export async function updateEducation(id: string, data: any) {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/api/v1/candidates/education/${id}/`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to update education')
    }

    revalidatePath('/dashboard/profile')
    return await response.json()
  } catch (error: any) {
    throw new Error(error.message || 'Failed to update education')
  }
}

export async function deleteEducation(id: string) {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/api/v1/candidates/education/${id}/`, {
      method: 'DELETE',
      headers,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to delete education')
    }

    revalidatePath('/dashboard/profile')
    return { success: true }
  } catch (error: any) {
    throw new Error(error.message || 'Failed to delete education')
  }
}

// Skills Actions

export async function createSkill(data: any) {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/api/v1/candidates/skills/`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to create skill')
    }

    revalidatePath('/dashboard/profile')
    return await response.json()
  } catch (error: any) {
    throw new Error(error.message || 'Failed to create skill')
  }
}

export async function deleteSkill(id: string) {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/api/v1/candidates/skills/${id}/`, {
      method: 'DELETE',
      headers,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to delete skill')
    }

    revalidatePath('/dashboard/profile')
    return { success: true }
  } catch (error: any) {
    throw new Error(error.message || 'Failed to delete skill')
  }
}
