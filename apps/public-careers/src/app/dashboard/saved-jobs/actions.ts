'use server'

import { revalidatePath } from 'next/cache'
import { verifySession } from '@/lib/auth'
import { saveJob, unsaveJob } from '@/lib/dal'

export interface SaveJobState {
  success: boolean
  message?: string
  savedJobId?: string
}

export async function saveJobAction(requisitionId: string): Promise<SaveJobState> {
  try {
    await verifySession()
    const data = await saveJob(requisitionId)
    revalidatePath('/dashboard/saved-jobs')
    revalidatePath('/jobs')
    return { success: true, savedJobId: data.id }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to save job'
    return { success: false, message }
  }
}

export async function unsaveJobAction(savedJobId: string): Promise<SaveJobState> {
  try {
    await verifySession()
    await unsaveJob(savedJobId)
    revalidatePath('/dashboard/saved-jobs')
    revalidatePath('/jobs')
    return { success: true }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to remove saved job'
    return { success: false, message }
  }
}
