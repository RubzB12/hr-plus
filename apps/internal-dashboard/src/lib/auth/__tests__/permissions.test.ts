/**
 * @jest-environment node
 */

import { requirePermission, hasPermission } from '../permissions'
import { getSession } from '../session'

// Mock getSession
jest.mock('../session')

const mockGetSession = getSession as jest.MockedFunction<typeof getSession>

// Test-only stub values — not real credentials
const TEST_ACCESS_TOKEN = 'test-token-stub'

describe('Auth Permissions', () => {
  const mockSession = {
    user: {
      id: '123',
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      is_internal: true,
      is_active: true,
    },
    accessToken: TEST_ACCESS_TOKEN,
    permissions: ['applications.view_application', 'candidates.view_candidate', 'offers.create_offer'],
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('hasPermission', () => {
    it('should return true when user has the permission', async () => {
      mockGetSession.mockResolvedValue(mockSession)

      const result = await hasPermission('applications.view_application')

      expect(result).toBe(true)
    })

    it('should return false when user does not have the permission', async () => {
      mockGetSession.mockResolvedValue(mockSession)

      const result = await hasPermission('users.delete_user')

      expect(result).toBe(false)
    })

    it('should return false when session is null', async () => {
      mockGetSession.mockResolvedValue(null)

      const result = await hasPermission('applications.view_application')

      expect(result).toBe(false)
    })

    it('should return false when permissions array is undefined', async () => {
      mockGetSession.mockResolvedValue({
        ...mockSession,
        permissions: undefined as any,
      })

      const result = await hasPermission('applications.view_application')

      expect(result).toBe(false)
    })
  })

  describe('requirePermission', () => {
    it('should return session when user has the permission', async () => {
      mockGetSession.mockResolvedValue(mockSession)

      const session = await requirePermission('applications.view_application')

      expect(session).toEqual(mockSession)
    })

    it('should throw error when user does not have the permission', async () => {
      mockGetSession.mockResolvedValue(mockSession)

      await expect(requirePermission('users.delete_user')).rejects.toThrow(
        "Forbidden: Missing permission 'users.delete_user'"
      )
    })

    it('should throw error when session is null', async () => {
      mockGetSession.mockResolvedValue(null)

      await expect(requirePermission('applications.view_application')).rejects.toThrow('Unauthorized')
    })

    it('should throw error when user object is missing', async () => {
      mockGetSession.mockResolvedValue({
        ...mockSession,
        user: undefined as any,
      })

      await expect(requirePermission('applications.view_application')).rejects.toThrow('Unauthorized')
    })
  })
})
