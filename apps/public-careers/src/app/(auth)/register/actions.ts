'use server'

import { z } from 'zod'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

const API_URL = process.env.DJANGO_API_URL

const RegisterSchema = z
  .object({
    first_name: z.string().min(1, 'First name is required').max(150),
    last_name: z.string().min(1, 'Last name is required').max(150),
    email: z.string().email('Please enter a valid email address'),
    password: z
      .string()
      .min(10, 'Password must be at least 10 characters'),
    confirm_password: z.string(),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  })

export interface RegisterState {
  success: boolean
  errors?: Record<string, string[]>
  message?: string
}

export async function registerAction(
  _prevState: RegisterState,
  formData: FormData
): Promise<RegisterState> {
  const validatedFields = RegisterSchema.safeParse({
    first_name: formData.get('first_name'),
    last_name: formData.get('last_name'),
    email: formData.get('email'),
    password: formData.get('password'),
    confirm_password: formData.get('confirm_password'),
  })

  if (!validatedFields.success) {
    return {
      success: false,
      errors: validatedFields.error.flatten().fieldErrors as Record<string, string[]>,
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { confirm_password, ...payload } = validatedFields.data

  const res = await fetch(`${API_URL}/api/v1/auth/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const error = await res.json()
    return {
      success: false,
      errors: typeof error === 'object' ? error : undefined,
      message:
        typeof error === 'string'
          ? error
          : error.detail ?? 'Registration failed. Please try again.',
    }
  }

  const data = await res.json()

  if (data.token) {
    const cookieStore = await cookies()
    cookieStore.set('session', data.token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
    })
    redirect('/dashboard/profile')
  }

  redirect('/login?registered=true')
}
