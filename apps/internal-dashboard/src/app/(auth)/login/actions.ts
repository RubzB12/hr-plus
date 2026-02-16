'use server'

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { z } from 'zod'

const LoginSchema = z.object({
  email: z.email(),
  password: z.string().min(1, 'Password is required'),
})

type LoginState = {
  error?: string
} | null

export async function loginAction(
  _prevState: LoginState,
  formData: FormData
): Promise<LoginState> {
  const parsed = LoginSchema.safeParse({
    email: formData.get('email'),
    password: formData.get('password'),
  })

  if (!parsed.success) {
    return { error: 'Please enter a valid email and password.' }
  }

  const apiUrl = process.env.DJANGO_API_URL

  try {
    const response = await fetch(`${apiUrl}/api/v1/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parsed.data),
      credentials: 'include',
    })

    if (!response.ok) {
      return { error: 'Invalid email or password.' }
    }

  // Extract session cookie from Django response and set it
  const setCookieHeader = response.headers.get('set-cookie')
  console.log('🔐 Login Debug:', {
    setCookieHeader,
    allHeaders: Array.from(response.headers.entries()),
  })

  if (setCookieHeader) {
    const cookieStore = await cookies()
    // Parse the sessionid from Django's set-cookie header
    const sessionMatch = setCookieHeader.match(/sessionid=([^;]+)/)
    console.log('🔐 Session Match:', sessionMatch)
    if (sessionMatch) {
      cookieStore.set('session', sessionMatch[1], {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        path: '/',
        maxAge: 86400, // 24 hours
      })
      console.log('✅ Session cookie set:', sessionMatch[1])
    } else {
      console.error('❌ No sessionid found in Set-Cookie header')
    }
  } else {
    console.error('❌ No Set-Cookie header in response')
  }

    redirect('/dashboard')
  } catch (error) {
    // Re-throw redirect errors (Next.js uses these for navigation)
    if (error instanceof Error && error.message === 'NEXT_REDIRECT') {
      throw error
    }
    console.error('Login error:', error)
    return { error: 'Invalid email or password.' }
  }
}
