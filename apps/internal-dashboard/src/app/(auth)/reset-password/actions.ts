'use server'

import { z } from 'zod'

const ResetPasswordSchema = z
  .object({
    token: z.string().min(1, 'Invalid reset token'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string().min(8, 'Password must be at least 8 characters'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  })

type ResetPasswordState = {
  success?: boolean
  error?: string
} | null

export async function resetPasswordAction(
  _prevState: ResetPasswordState,
  formData: FormData
): Promise<ResetPasswordState> {
  const parsed = ResetPasswordSchema.safeParse({
    token: formData.get('token'),
    password: formData.get('password'),
    confirmPassword: formData.get('confirmPassword'),
  })

  if (!parsed.success) {
    const errors = parsed.error.flatten().fieldErrors
    const firstError =
      errors.password?.[0] || errors.confirmPassword?.[0] || errors.token?.[0]
    return { error: firstError || 'Invalid input' }
  }

  const apiUrl = process.env.DJANGO_API_URL

  try {
    const response = await fetch(`${apiUrl}/api/v1/auth/password-reset/confirm/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: parsed.data.token,
        new_password: parsed.data.password,
      }),
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      return {
        error:
          data.detail || 'Failed to reset password. The link may have expired.',
      }
    }

    return { success: true }
  } catch (error) {
    return { error: 'Something went wrong. Please try again later.' }
  }
}
