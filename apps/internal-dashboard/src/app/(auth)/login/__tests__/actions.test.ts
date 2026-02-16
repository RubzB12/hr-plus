/**
 * @jest-environment node
 */

import { loginAction } from '../actions'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

jest.mock('next/headers')
jest.mock('next/navigation')

const mockCookies = cookies as jest.MockedFunction<typeof cookies>
const mockRedirect = redirect as jest.MockedFunction<typeof redirect>

describe('Login Action', () => {
  let mockCookieStore: any

  beforeEach(() => {
    jest.clearAllMocks()
    global.fetch = jest.fn()

    mockCookieStore = {
      get: jest.fn(),
      set: jest.fn(),
      delete: jest.fn(),
      getAll: jest.fn(),
    }

    mockCookies.mockReturnValue(mockCookieStore)
  })

  it('should validate email format', async () => {
    const formData = new FormData()
    formData.set('email', 'invalid-email')
    formData.set('password', 'password123')

    const result = await loginAction(null, formData)

    expect(result).toEqual({
      error: 'Please enter a valid email and password.',
    })
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('should validate password is not empty', async () => {
    const formData = new FormData()
    formData.set('email', 'test@example.com')
    formData.set('password', '')

    const result = await loginAction(null, formData)

    expect(result).toEqual({
      error: 'Please enter a valid email and password.',
    })
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('should return error for invalid credentials', async () => {
    const formData = new FormData()
    formData.set('email', 'test@example.com')
    formData.set('password', 'wrongpassword')

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 401,
    })

    const result = await loginAction(null, formData)

    expect(result).toEqual({
      error: 'Invalid email or password.',
    })

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/auth/login/'),
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      })
    )
  })

  it('should set session cookie and redirect on successful login', async () => {
    const formData = new FormData()
    formData.set('email', 'test@example.com')
    formData.set('password', 'password123')

    const mockHeaders = new Headers()
    mockHeaders.set('set-cookie', 'sessionid=test-session-123; Path=/; HttpOnly')

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      headers: mockHeaders,
    })

    mockRedirect.mockImplementation(() => {
      throw new Error('NEXT_REDIRECT')
    })

    await expect(loginAction(null, formData)).rejects.toThrow('NEXT_REDIRECT')

    expect(mockCookieStore.set).toHaveBeenCalledWith(
      'session',
      'test-session-123',
      expect.objectContaining({
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
      })
    )

    expect(mockRedirect).toHaveBeenCalledWith('/dashboard')
  })

  it('should handle network errors', async () => {
    const formData = new FormData()
    formData.set('email', 'test@example.com')
    formData.set('password', 'password123')

    ;(global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

    const result = await loginAction(null, formData)

    expect(result).toEqual({
      error: 'Invalid email or password.',
    })
  })

  it('should use correct environment variable for API URL', async () => {
    const originalEnv = process.env.DJANGO_API_URL
    process.env.DJANGO_API_URL = 'https://test-api.example.com'

    const formData = new FormData()
    formData.set('email', 'test@example.com')
    formData.set('password', 'password123')

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
    })

    await loginAction(null, formData)

    expect(global.fetch).toHaveBeenCalledWith(
      'https://test-api.example.com/api/v1/auth/login/',
      expect.any(Object)
    )

    process.env.DJANGO_API_URL = originalEnv
  })
})
