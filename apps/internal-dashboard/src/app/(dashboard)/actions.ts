'use server'

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

export async function logoutAction() {
  const cookieStore = await cookies()
  const session = cookieStore.get('internal_session')

  if (session) {
    const apiUrl = process.env.DJANGO_API_URL
    // Notify Django of logout
    await fetch(`${apiUrl}/api/v1/auth/logout/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${session.value}`,
      },
    }).catch(() => {
      // Best-effort logout on Django side
    })
  }

  const store = await cookies()
  store.delete('internal_session')
  redirect('/login')
}
