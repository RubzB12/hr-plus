'use server'

import { z } from 'zod'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

const API_URL = process.env.DJANGO_API_URL

const LoginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})

export interface LoginState {
  success: boolean
  errors?: Record<string, string[]>
  message?: string
}

export async function loginAction(
  _prevState: LoginState,
  formData: FormData
): Promise<LoginState> {
  const validatedFields = LoginSchema.safeParse({
    email: formData.get('email'),
    password: formData.get('password'),
  })

  if (!validatedFields.success) {
    return {
      success: false,
      errors: validatedFields.error.flatten().fieldErrors as Record<string, string[]>,
    }
  }

  const res = await fetch(`${API_URL}/api/v1/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(validatedFields.data),
  })

  if (!res.ok) {
    const error = await res.json()
    return {
      success: false,
      message: error.detail ?? error.non_field_errors?.[0] ?? 'Invalid email or password.',
    }
  }

  const data = await res.json()

  const cookieStore = await cookies()
  cookieStore.set('session', data.token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
  })

  redirect('/dashboard/applications')
}
