'use server'

import { z } from 'zod'
import { revalidatePath } from 'next/cache'
import { verifySession } from '@/lib/auth'
import { confirmInterview } from '@/lib/dal'

const Schema = z.object({
  interviewId: z.string().uuid('Invalid interview ID'),
})

export interface ConfirmInterviewState {
  success: boolean
  message?: string
}

export async function confirmInterviewAction(interviewId: string): Promise<ConfirmInterviewState> {
  try {
    await verifySession()
  } catch {
    return { success: false, message: 'Please log in to confirm your interview.' }
  }

  const validated = Schema.safeParse({ interviewId })
  if (!validated.success) {
    return { success: false, message: 'Invalid interview reference.' }
  }

  try {
    await confirmInterview(validated.data.interviewId)
    revalidatePath('/dashboard/interviews')
    return { success: true, message: 'Attendance confirmed!' }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to confirm interview'
    let parsed: Record<string, unknown> | undefined
    try {
      parsed = JSON.parse(message)
    } catch {
      // not JSON
    }
    const detail = (parsed as any)?.detail ?? message
    return { success: false, message: typeof detail === 'string' ? detail : 'Failed to confirm interview.' }
  }
}
