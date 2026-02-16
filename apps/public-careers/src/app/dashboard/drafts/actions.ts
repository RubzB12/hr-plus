'use server'

import { revalidatePath } from 'next/cache'
import {
  submitDraft as submitDraftDAL,
  deleteDraft as deleteDraftDAL
} from '@/lib/dal'

export async function submitDraftAction(draftId: string) {
  try {
    const result = await submitDraftDAL(draftId)
    revalidatePath('/dashboard/drafts')
    revalidatePath('/dashboard/applications')
    return { success: true, data: result }
  } catch (error) {
    console.error('Failed to submit draft:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to submit draft'
    }
  }
}

export async function deleteDraftAction(draftId: string) {
  try {
    await deleteDraftDAL(draftId)
    revalidatePath('/dashboard/drafts')
    return { success: true }
  } catch (error) {
    console.error('Failed to delete draft:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to delete draft'
    }
  }
}
