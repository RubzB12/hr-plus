'use server'

import { z } from 'zod'

const ForgotPasswordSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
})

type ForgotPasswordState = {
  success?: boolean
  message?: string
  error?: string
} | null

export async function forgotPasswordAction(
  _prevState: ForgotPasswordState,
  formData: FormData
): Promise<ForgotPasswordState> {
  const parsed = ForgotPasswordSchema.safeParse({
    email: formData.get('email'),
  })

  if (!parsed.success) {
    const errors = parsed.error.flatten().fieldErrors
    return { error: errors.email?.[0] || 'Please enter a valid email address' }
  }

  const apiUrl = process.env.DJANGO_API_URL

  try {
    const response = await fetch(`${apiUrl}/api/v1/auth/password-reset/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: parsed.data.email }),
    })

    if (!response.ok) {
      return { error: 'Failed to send reset email. Please try again.' }
    }

    return {
      success: true,
      message: 'If an account exists with that email, you will receive a password reset link.',
    }
  } catch (error) {
    return { error: 'Something went wrong. Please try again later.' }
  }
}
