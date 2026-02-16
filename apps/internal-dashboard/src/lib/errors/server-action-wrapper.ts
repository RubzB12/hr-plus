'use server'

import { ZodSchema } from 'zod'
import { logError, parseApiError, isRedirectError, formatZodError } from './error-handler'

export type ActionResult<T = any> =
  | { success: true; data: T }
  | { success: false; error: string; fields?: Record<string, string[]> }

/**
 * Wrapper for Server Actions with standardized error handling and validation
 *
 * @example
 * export const createOffer = actionWrapper({
 *   schema: CreateOfferSchema,
 *   action: async (data, context) => {
 *     const offer = await api.post('/api/v1/offers/', data)
 *     revalidatePath('/offers')
 *     return offer
 *   },
 *   errorMessage: 'Failed to create offer',
 * })
 */
export function actionWrapper<TInput, TOutput>(config: {
  schema?: ZodSchema<TInput>
  action: (data: TInput, context?: any) => Promise<TOutput>
  errorMessage?: string
  logContext?: Record<string, any>
}) {
  return async (data: TInput, context?: any): Promise<ActionResult<TOutput>> => {
    try {
      // Validate input if schema provided
      if (config.schema) {
        const validation = config.schema.safeParse(data)

        if (!validation.success) {
          const fields = formatZodError(validation.error)
          const firstError = Object.values(fields)[0]?.[0] || 'Validation failed'

          return {
            success: false,
            error: firstError,
            fields,
          }
        }
      }

      // Execute action
      const result = await config.action(data, context)

      return {
        success: true,
        data: result,
      }
    } catch (error) {
      // Re-throw redirect errors (Next.js navigation)
      if (isRedirectError(error)) {
        throw error
      }

      // Log error
      logError(error as Error, {
        ...config.logContext,
        actionData: data,
      })

      // Parse and return error message
      const message = config.errorMessage || parseApiError(error)

      return {
        success: false,
        error: message,
      }
    }
  }
}

/**
 * Wrapper for form-based Server Actions (compatible with useActionState)
 *
 * @example
 * export const createOfferAction = formActionWrapper({
 *   schema: CreateOfferFormSchema,
 *   action: async (data) => {
 *     const offer = await api.post('/api/v1/offers/', data)
 *     redirect(`/offers/${offer.id}`)
 *   },
 *   errorMessage: 'Failed to create offer',
 * })
 */
export function formActionWrapper<TInput>(config: {
  schema?: ZodSchema<TInput>
  action: (data: TInput) => Promise<void | any>
  errorMessage?: string
  logContext?: Record<string, any>
  transformFormData?: (formData: FormData) => TInput
}) {
  return async (
    _prevState: any,
    formData: FormData
  ): Promise<ActionResult> => {
    try {
      // Transform FormData to input data
      const data = config.transformFormData
        ? config.transformFormData(formData)
        : Object.fromEntries(formData) as TInput

      // Validate input if schema provided
      if (config.schema) {
        const validation = config.schema.safeParse(data)

        if (!validation.success) {
          const fields = formatZodError(validation.error)
          const firstError = Object.values(fields)[0]?.[0] || 'Validation failed'

          return {
            success: false,
            error: firstError,
            fields,
          }
        }
      }

      // Execute action
      const result = await config.action(data)

      return {
        success: true,
        data: result,
      }
    } catch (error) {
      // Re-throw redirect errors (Next.js navigation)
      if (isRedirectError(error)) {
        throw error
      }

      // Log error
      logError(error as Error, {
        ...config.logContext,
      })

      // Parse and return error message
      const message = config.errorMessage || parseApiError(error)

      return {
        success: false,
        error: message,
      }
    }
  }
}
