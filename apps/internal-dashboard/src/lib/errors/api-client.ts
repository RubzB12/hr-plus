import 'server-only'

import { cookies } from 'next/headers'
import { parseApiError, logError, retryWithBackoff } from './error-handler'

const API_URL = process.env.DJANGO_API_URL

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function getAuthHeaders() {
  const cookieStore = await cookies()
  const sessionCookie = cookieStore.get('session')

  if (!sessionCookie) {
    throw new ApiError('Unauthorized - No session cookie found', 401)
  }

  return {
    'Content-Type': 'application/json',
    Cookie: `sessionid=${sessionCookie.value}`,
  }
}

interface ApiRequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: any
  requireAuth?: boolean
  retries?: number
  cache?: RequestCache
  revalidate?: number | false
}

/**
 * Centralized API client with error handling, retries, and logging
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const {
    method = 'GET',
    body,
    requireAuth = true,
    retries = 0,
    cache = 'no-store',
    revalidate,
  } = options

  const makeRequest = async (): Promise<T> => {
    try {
      const headers: HeadersInit = requireAuth
        ? await getAuthHeaders()
        : { 'Content-Type': 'application/json' }

      const fetchOptions: RequestInit = {
        method,
        headers,
        cache,
        ...(revalidate !== undefined && { next: { revalidate } }),
      }

      if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        fetchOptions.body = JSON.stringify(body)
      }

      const response = await fetch(`${API_URL}${endpoint}`, fetchOptions)

      // Handle successful responses
      if (response.ok) {
        // Handle no-content responses
        if (response.status === 204) {
          return null as T
        }

        const contentType = response.headers.get('content-type')
        if (contentType && contentType.includes('application/json')) {
          return await response.json()
        }

        return await response.text() as T
      }

      // Handle error responses
      let errorData: any
      try {
        errorData = await response.json()
      } catch {
        errorData = { detail: response.statusText }
      }

      const error = new ApiError(
        parseApiError(errorData),
        response.status,
        errorData
      )

      // Log error
      logError(error, {
        endpoint,
        method,
        status: response.status,
        errorData,
      })

      throw error
    } catch (error) {
      // Re-throw ApiError as-is
      if (error instanceof ApiError) {
        throw error
      }

      // Handle network errors
      if (error instanceof TypeError) {
        const networkError = new ApiError(
          'Unable to connect to the server. Please check your internet connection.',
          0
        )
        logError(networkError, { endpoint, method, originalError: error })
        throw networkError
      }

      // Handle other errors
      const unknownError = new ApiError(
        'An unexpected error occurred',
        500
      )
      logError(unknownError, { endpoint, method, originalError: error })
      throw unknownError
    }
  }

  // Use retry logic if specified
  if (retries > 0) {
    return await retryWithBackoff(makeRequest, retries)
  }

  return await makeRequest()
}

/**
 * Convenience methods for common HTTP methods
 */
export const api = {
  get: <T = any>(endpoint: string, options?: Omit<ApiRequestOptions, 'method' | 'body'>) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),

  post: <T = any>(endpoint: string, body?: any, options?: Omit<ApiRequestOptions, 'method' | 'body'>) =>
    apiRequest<T>(endpoint, { ...options, method: 'POST', body }),

  put: <T = any>(endpoint: string, body?: any, options?: Omit<ApiRequestOptions, 'method' | 'body'>) =>
    apiRequest<T>(endpoint, { ...options, method: 'PUT', body }),

  patch: <T = any>(endpoint: string, body?: any, options?: Omit<ApiRequestOptions, 'method' | 'body'>) =>
    apiRequest<T>(endpoint, { ...options, method: 'PATCH', body }),

  delete: <T = any>(endpoint: string, options?: Omit<ApiRequestOptions, 'method' | 'body'>) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),
}
