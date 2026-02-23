'use server'

import { z } from 'zod'
import { revalidatePath } from 'next/cache'
import { verifySession } from '@/lib/auth'
import { createApplication } from '@/lib/dal'

const Schema = z.object({
  requisitionId: z.string().uuid('Invalid job ID'),
})

export interface QuickApplyState {
  success: boolean
  message?: string
  applicationId?: string
}

export async function quickApplyAction(requisitionId: string): Promise<QuickApplyState> {
  try {
    await verifySession()
  } catch {
    return { success: false, message: 'Please log in to apply.' }
  }

  const validated = Schema.safeParse({ requisitionId })
  if (!validated.success) {
    return { success: false, message: 'Invalid job reference.' }
  }

  try {
    const application = await createApplication({
      requisition_id: validated.data.requisitionId,
      source: 'career_site',
    })
    revalidatePath('/dashboard/applications')
    return { success: true, applicationId: application.id, message: 'Application submitted successfully!' }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to submit application'
    let parsed: Record<string, unknown> | undefined
    try {
      parsed = JSON.parse(message)
    } catch {
      // not JSON
    }
    const detail = (parsed as any)?.detail ?? (parsed as any)?.non_field_errors?.[0] ?? message
    return { success: false, message: typeof detail === 'string' ? detail : 'Failed to submit application.' }
  }
}
