import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

const API_URL = process.env.DJANGO_API_URL

export async function POST() {
  const cookieStore = await cookies()
  const sessionCookie = cookieStore.get('session')
  if (!sessionCookie) {
    return NextResponse.json({ detail: 'Unauthorized' }, { status: 401 })
  }

  try {
    const res = await fetch(`${API_URL}/api/v1/notifications/mark-all-read/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${sessionCookie.value}`,
      },
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch {
    return NextResponse.json({ detail: 'Failed' }, { status: 500 })
  }
}
