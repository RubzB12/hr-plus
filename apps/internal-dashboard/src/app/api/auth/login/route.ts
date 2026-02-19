import { NextRequest, NextResponse } from 'next/server'

const API_URL = process.env.DJANGO_API_URL

export async function POST(request: NextRequest) {
  let body: { email?: string; password?: string }

  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Invalid request.' }, { status: 400 })
  }

  if (!body.email || !body.password) {
    return NextResponse.json({ error: 'Email and password are required.' }, { status: 400 })
  }

  try {
    const djangoResponse = await fetch(`${API_URL}/api/v1/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: body.email, password: body.password }),
    })

    if (!djangoResponse.ok) {
      return NextResponse.json({ error: 'Invalid email or password.' }, { status: 401 })
    }

    const data = await djangoResponse.json()

    if (!data.is_internal) {
      return NextResponse.json(
        { error: 'This account is not an internal account. Please use the candidate portal to log in.' },
        { status: 403 }
      )
    }

    const response = NextResponse.json({ success: true })
    response.cookies.set('internal_session', data.token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 86400, // 24 hours
    })

    return response
  } catch {
    return NextResponse.json({ error: 'Unable to connect to the server. Please try again.' }, { status: 500 })
  }
}
