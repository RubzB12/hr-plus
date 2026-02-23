import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

const API_URL = process.env.DJANGO_API_URL

export async function GET() {
  const cookieStore = await cookies()
  const sessionCookie = cookieStore.get('session')
  if (!sessionCookie) {
    return NextResponse.json({ count: 0 })
  }

  try {
    const res = await fetch(`${API_URL}/api/v1/notifications/unread-count/`, {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${sessionCookie.value}`,
      },
      cache: 'no-store',
    })
    if (!res.ok) return NextResponse.json({ count: 0 })
    const data = await res.json()
    return NextResponse.json({ count: data.count ?? 0 })
  } catch {
    return NextResponse.json({ count: 0 })
  }
}
