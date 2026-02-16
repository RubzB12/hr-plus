/**
 * Centralized error handling utilities
 */

export class AppError extends Error {
  constructor(
    message: string,
    public code?: string,
    public statusCode?: number,
    public details?: Record<string, any>
  ) {
    super(message)
    this.name = 'AppError'
  }
}

export class ValidationError extends AppError {
  constructor(message: string, public fields?: Record<string, string[]>) {
    super(message, 'VALIDATION_ERROR', 400)
    this.name = 'ValidationError'
  }
}

export class AuthenticationError extends AppError {
  constructor(message: string = 'Authentication required') {
    super(message, 'AUTH_ERROR', 401)
    this.name = 'AuthenticationError'
  }
}

export class AuthorizationError extends AppError {
  constructor(message: string = 'Insufficient permissions') {
    super(message, 'FORBIDDEN', 403)
    this.name = 'AuthorizationError'
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string = 'Resource') {
    super(`${resource} not found`, 'NOT_FOUND', 404)
    this.name = 'NotFoundError'
  }
}

export class ServerError extends AppError {
  constructor(message: string = 'An unexpected error occurred') {
    super(message, 'SERVER_ERROR', 500)
    this.name = 'ServerError'
  }
}

/**
 * Parse API error response and return user-friendly message
 */
export function parseApiError(error: any): string {
  // Handle fetch errors
  if (error instanceof TypeError && error.message === 'Failed to fetch') {
    return 'Unable to connect to the server. Please check your internet connection.'
  }

  // Handle Response object
  if (error instanceof Response) {
    switch (error.status) {
      case 400:
        return 'Invalid request. Please check your input and try again.'
      case 401:
        return 'Your session has expired. Please log in again.'
      case 403:
        return 'You do not have permission to perform this action.'
      case 404:
        return 'The requested resource was not found.'
      case 409:
        return 'This action conflicts with existing data.'
      case 422:
        return 'The data provided is invalid.'
      case 429:
        return 'Too many requests. Please try again later.'
      case 500:
        return 'A server error occurred. Please try again later.'
      case 503:
        return 'The service is temporarily unavailable. Please try again later.'
      default:
        return 'An unexpected error occurred. Please try again.'
    }
  }

  // Handle JSON error responses
  if (error?.detail) {
    return typeof error.detail === 'string' ? error.detail : 'An error occurred'
  }

  if (error?.message) {
    return error.message
  }

  // Handle validation errors
  if (error?.errors && typeof error.errors === 'object') {
    const firstError = Object.values(error.errors)[0]
    if (Array.isArray(firstError) && firstError.length > 0) {
      return firstError[0]
    }
  }

  return 'An unexpected error occurred. Please try again.'
}

/**
 * Log error to monitoring service (Sentry, LogRocket, etc.)
 */
export function logError(error: Error, context?: Record<string, any>) {
  // In development, log to console
  if (process.env.NODE_ENV === 'development') {
    console.error('Error logged:', {
      error,
      message: error.message,
      stack: error.stack,
      context,
    })
    return
  }

  // In production, send to monitoring service
  // TODO: Integrate with Sentry or similar service
  try {
    // Example Sentry integration:
    // Sentry.captureException(error, { extra: context })

    console.error('Error occurred:', {
      message: error.message,
      name: error.name,
      context,
    })
  } catch (loggingError) {
    console.error('Failed to log error:', loggingError)
  }
}

/**
 * Handle async errors in Server Actions
 */
export async function handleServerActionError<T>(
  action: () => Promise<T>,
  errorMessage?: string
): Promise<{ success: true; data: T } | { success: false; error: string }> {
  try {
    const data = await action()
    return { success: true, data }
  } catch (error) {
    logError(error as Error)

    const message = errorMessage || parseApiError(error)
    return { success: false, error: message }
  }
}

/**
 * Extract validation errors from Zod error
 */
export function formatZodError(error: any): Record<string, string[]> {
  if (error?.flatten) {
    const flattened = error.flatten()
    return flattened.fieldErrors || {}
  }
  return {}
}

/**
 * Check if error is a redirect (Next.js navigation)
 */
export function isRedirectError(error: any): boolean {
  return (
    error instanceof Error &&
    (error.message === 'NEXT_REDIRECT' || error.message.includes('NEXT_REDIRECT'))
  )
}

/**
 * Retry a function with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  let lastError: Error | undefined

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error

      // Don't retry on these errors
      if (
        error instanceof AuthenticationError ||
        error instanceof AuthorizationError ||
        error instanceof ValidationError
      ) {
        throw error
      }

      if (attempt < maxRetries) {
        const delay = baseDelay * Math.pow(2, attempt)
        await new Promise((resolve) => setTimeout(resolve, delay))
      }
    }
  }

  throw lastError || new Error('Max retries exceeded')
}
