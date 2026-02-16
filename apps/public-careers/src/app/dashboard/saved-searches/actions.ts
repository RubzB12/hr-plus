'use server'

import { revalidatePath } from 'next/cache'
import {
  createSavedSearch as createSavedSearchDAL,
  deleteSavedSearch as deleteSavedSearchDAL,
  toggleSavedSearchAlerts as toggleSavedSearchAlertsDAL
} from '@/lib/dal'
import type { SearchParams } from '@/types/api'

export async function createSavedSearchAction(data: {
  name: string
  search_params: SearchParams
  alert_frequency: string
}) {
  try {
    const result = await createSavedSearchDAL(data)
    revalidatePath('/dashboard/saved-searches')
    return { success: true, data: result }
  } catch (error) {
    console.error('Failed to create saved search:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to create saved search'
    }
  }
}

export async function deleteSavedSearchAction(id: string) {
  try {
    await deleteSavedSearchDAL(id)
    revalidatePath('/dashboard/saved-searches')
    return { success: true }
  } catch (error) {
    console.error('Failed to delete saved search:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to delete saved search'
    }
  }
}

export async function toggleSavedSearchAlertsAction(id: string) {
  try {
    const result = await toggleSavedSearchAlertsDAL(id)
    revalidatePath('/dashboard/saved-searches')
    return { success: true, data: result }
  } catch (error) {
    console.error('Failed to toggle alerts:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to toggle alerts'
    }
  }
}
