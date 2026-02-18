'use server'

import { z } from 'zod'
import { redirect } from 'next/navigation'
import { verifySession } from '@/lib/auth'
import { createApplication } from '@/lib/dal'

const ApplySchema = z.object({
  requisition_id: z.string().min(1, 'Requisition ID is required'),
  cover_letter: z.string().max(5000).optional().default(''),
  screening_responses: z.string().optional().default('{}'),
  source: z.string().optional().default('career_site'),
})

export interface ApplyState {
  success: boolean
  errors?: Record<string, string[]>
  message?: string
}

export async function applyAction(
  _prevState: ApplyState,
  formData: FormData
): Promise<ApplyState> {
  await verifySession()

  const validatedFields = ApplySchema.safeParse({
    requisition_id: formData.get('requisition_id'),
    cover_letter: formData.get('cover_letter') || '',
    screening_responses: formData.get('screening_responses') || '{}',
    source: 'career_site',
  })

  if (!validatedFields.success) {
    return {
      success: false,
      errors: validatedFields.error.flatten().fieldErrors as Record<string, string[]>,
    }
  }

  let screeningResponses: Record<string, string> = {}
  try {
    screeningResponses = JSON.parse(validatedFields.data.screening_responses)
  } catch {
    // ignore parse error, send empty
  }

  try {
    await createApplication({
      requisition_id: validatedFields.data.requisition_id,
      cover_letter: validatedFields.data.cover_letter || undefined,
      screening_responses:
        Object.keys(screeningResponses).length > 0
          ? screeningResponses
          : undefined,
      source: validatedFields.data.source,
    })
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to submit application.'
    let parsed: Record<string, unknown> | undefined
    try {
      parsed = JSON.parse(message)
    } catch {
      // not JSON
    }

    // DRF returns {detail: "..."} for top-level errors (auth, permission, etc.)
    if (parsed?.detail) {
      const detail = String(parsed.detail)
      return {
        success: false,
        message: detail.includes('already applied')
          ? 'You have already applied to this position.'
          : detail.includes('permission')
            ? 'You must complete your candidate profile before applying.'
            : detail,
      }
    }

    // DRF field validation errors: {field: ["error", ...]}
    const fieldErrors = parsed as Record<string, string[]> | undefined
    return {
      success: false,
      errors: fieldErrors,
      message: fieldErrors
        ? undefined
        : message.includes('already applied')
          ? 'You have already applied to this position.'
          : message,
    }
  }

  redirect('/dashboard/applications')
}
