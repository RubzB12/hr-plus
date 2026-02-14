'use server'

import { z } from 'zod'
import { revalidatePath } from 'next/cache'
import { verifySession } from '@/lib/auth'
import { updateProfile } from '@/lib/dal'

const ProfileSchema = z.object({
  first_name: z.string().min(1, 'First name is required').max(150),
  last_name: z.string().min(1, 'Last name is required').max(150),
  phone: z.string().max(20).optional().default(''),
  location_city: z.string().max(100).optional().default(''),
  location_country: z.string().max(100).optional().default(''),
  work_authorization: z.string().max(100).optional().default(''),
  linkedin_url: z
    .string()
    .url('Please enter a valid URL')
    .or(z.literal(''))
    .optional()
    .default(''),
  portfolio_url: z
    .string()
    .url('Please enter a valid URL')
    .or(z.literal(''))
    .optional()
    .default(''),
})

export interface ProfileState {
  success: boolean
  errors?: Record<string, string[]>
  message?: string
}

export async function updateProfileAction(
  _prevState: ProfileState,
  formData: FormData
): Promise<ProfileState> {
  await verifySession()

  const validatedFields = ProfileSchema.safeParse({
    first_name: formData.get('first_name'),
    last_name: formData.get('last_name'),
    phone: formData.get('phone') || '',
    location_city: formData.get('location_city') || '',
    location_country: formData.get('location_country') || '',
    work_authorization: formData.get('work_authorization') || '',
    linkedin_url: formData.get('linkedin_url') || '',
    portfolio_url: formData.get('portfolio_url') || '',
  })

  if (!validatedFields.success) {
    return {
      success: false,
      errors: validatedFields.error.flatten().fieldErrors as Record<string, string[]>,
    }
  }

  try {
    await updateProfile(validatedFields.data)
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to update profile.'
    let parsed: Record<string, string[]> | undefined
    try {
      parsed = JSON.parse(message)
    } catch {
      // not JSON
    }
    return {
      success: false,
      errors: parsed,
      message: parsed ? undefined : message,
    }
  }

  revalidatePath('/dashboard/profile')
  return { success: true, message: 'Profile updated successfully.' }
}
