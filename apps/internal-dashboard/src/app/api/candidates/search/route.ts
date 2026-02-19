import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env.DJANGO_API_URL

export async function GET(request: NextRequest) {
  const sessionCookie = request.cookies.get('internal_session')

  if (!sessionCookie) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { searchParams } = new URL(request.url)

  try {
    const djangoResponse = await fetch(
      `${API_URL}/api/v1/internal/candidates/search/?${searchParams}`,
      {
        headers: {
          'Content-Type': 'application/json',
          Cookie: `sessionid=${sessionCookie.value}`,
        },
        cache: 'no-store',
      },
    )

    if (!djangoResponse.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch candidates' },
        { status: djangoResponse.status },
      )
    }

    const data = await djangoResponse.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ error: 'Unable to connect to the server' }, { status: 500 })
  }
}
