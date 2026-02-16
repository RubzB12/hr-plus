/**
 * @jest-environment node
 */

import { resetPasswordAction } from '../actions'

describe('Reset Password Action', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    global.fetch = jest.fn()
  })

  it('should validate token presence', async () => {
    const formData = new FormData()
    formData.set('token', '')
    formData.set('password', 'newpassword123')
    formData.set('confirmPassword', 'newpassword123')

    const result = await resetPasswordAction(null, formData)

    expect(result?.error).toBeDefined()
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('should validate password minimum length', async () => {
    const formData = new FormData()
    formData.set('token', 'valid-token')
    formData.set('password', 'short')
    formData.set('confirmPassword', 'short')

    const result = await resetPasswordAction(null, formData)

    expect(result).toEqual({
      error: 'Password must be at least 8 characters',
    })
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('should validate passwords match', async () => {
    const formData = new FormData()
    formData.set('token', 'valid-token')
    formData.set('password', 'password123')
    formData.set('confirmPassword', 'different123')

    const result = await resetPasswordAction(null, formData)

    expect(result).toEqual({
      error: "Passwords don't match",
    })
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('should successfully reset password', async () => {
    const formData = new FormData()
    formData.set('token', 'valid-reset-token')
    formData.set('password', 'newpassword123')
    formData.set('confirmPassword', 'newpassword123')

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ detail: 'Password reset successful' }),
    })

    const result = await resetPasswordAction(null, formData)

    expect(result).toEqual({
      success: true,
    })

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/auth/password-reset/confirm/'),
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: 'valid-reset-token',
          new_password: 'newpassword123',
        }),
      })
    )
  })

  it('should handle expired token error', async () => {
    const formData = new FormData()
    formData.set('token', 'expired-token')
    formData.set('password', 'newpassword123')
    formData.set('confirmPassword', 'newpassword123')

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Invalid or expired token' }),
    })

    const result = await resetPasswordAction(null, formData)

    expect(result).toEqual({
      error: 'Invalid or expired token',
    })
  })

  it('should handle network errors', async () => {
    const formData = new FormData()
    formData.set('token', 'valid-token')
    formData.set('password', 'newpassword123')
    formData.set('confirmPassword', 'newpassword123')

    ;(global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

    const result = await resetPasswordAction(null, formData)

    expect(result).toEqual({
      error: 'Something went wrong. Please try again later.',
    })
  })
})
