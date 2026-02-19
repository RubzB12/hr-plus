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
  let token: string

  try {
    const response = await fetch(`${apiUrl}/api/v1/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parsed.data),
    })

    if (!response.ok) {
      return { error: 'Invalid email or password.' }
    }

    const data = await response.json()

    if (!data.is_internal) {
      return { error: 'This account is not an internal account. Please use the candidate portal to log in.' }
    }

    token = data.token
  } catch {
    return { error: 'Unable to connect to the server. Please try again.' }
  }

  // Set cookie and redirect OUTSIDE the try-catch so Next.js properly
  // flushes cookie mutations into the redirect response.
  const cookieStore = await cookies()
  cookieStore.set('internal_session', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 86400, // 24 hours
  })

  redirect('/dashboard')
}
