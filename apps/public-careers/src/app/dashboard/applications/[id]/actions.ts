'use server'

import { revalidatePath } from 'next/cache'
import { verifySession } from '@/lib/auth'
import { withdrawApplication } from '@/lib/dal'

export interface WithdrawState {
  success: boolean
  message?: string
}

export async function withdrawAction(
  _prevState: WithdrawState,
  formData: FormData
): Promise<WithdrawState> {
  await verifySession()

  const applicationId = formData.get('applicationId')
  if (typeof applicationId !== 'string' || !applicationId) {
    return { success: false, message: 'Invalid application ID.' }
  }

  const reason = formData.get('reason')
  const reasonStr = typeof reason === 'string' ? reason : ''

  try {
    await withdrawApplication(applicationId, reasonStr)
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to withdraw application.'
    return { success: false, message }
  }

  revalidatePath(`/dashboard/applications/${applicationId}`)
  revalidatePath('/dashboard/applications')
  return { success: true, message: 'Application withdrawn successfully.' }
}
