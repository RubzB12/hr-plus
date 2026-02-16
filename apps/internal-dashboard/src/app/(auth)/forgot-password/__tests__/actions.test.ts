/**
 * @jest-environment node
 */

import { forgotPasswordAction } from '../actions'

describe('Forgot Password Action', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    global.fetch = jest.fn()
  })

  it('should validate email format', async () => {
    const formData = new FormData()
    formData.set('email', 'invalid-email')

    const result = await forgotPasswordAction(null, formData)

    expect(result).toEqual({
      error: 'Please enter a valid email address',
    })
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('should return success message on valid email', async () => {
    const formData = new FormData()
    formData.set('email', 'test@example.com')

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ detail: 'Reset link sent' }),
    })

    const result = await forgotPasswordAction(null, formData)

    expect(result).toEqual({
      success: true,
      message: 'If an account exists with that email, you will receive a password reset link.',
    })

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/auth/password-reset/'),
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'test@example.com' }),
      })
    )
  })

  it('should return error message on API failure', async () => {
    const formData = new FormData()
    formData.set('email', 'test@example.com')

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
    })

    const result = await forgotPasswordAction(null, formData)

    expect(result).toEqual({
      error: 'Failed to send reset email. Please try again.',
    })
  })

  it('should handle network errors gracefully', async () => {
    const formData = new FormData()
    formData.set('email', 'test@example.com')

    ;(global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

    const result = await forgotPasswordAction(null, formData)

    expect(result).toEqual({
      error: 'Something went wrong. Please try again later.',
    })
  })
})
