import 'server-only'

import { cookies } from 'next/headers'

const API_URL = process.env.DJANGO_API_URL

export async function getSession() {
  const cookieStore = await cookies()
  const sessionCookie = cookieStore.get('session')

  if (!sessionCookie) {
    return null
  }

  try {
    const res = await fetch(`${API_URL}/api/v1/auth/me/`, {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${sessionCookie.value}`,
      },
      cache: 'no-store',
    })

    if (!res.ok) return null
    const user = await res.json()
    return { user, accessToken: sessionCookie.value }
  } catch {
    return null
  }
}

export async function verifySession() {
  const session = await getSession()
  if (!session?.user?.id) {
    throw new Error('Unauthorized')
  }
  return session
}
