/**
 * @jest-environment node
 */

import { getSession, requireAuth, requireInternalUser } from '../session'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

// Mock the dependencies
jest.mock('next/headers')
jest.mock('next/navigation')

const mockCookies = cookies as jest.MockedFunction<typeof cookies>
const mockRedirect = redirect as jest.MockedFunction<typeof redirect>

describe('Auth Session Helpers', () => {
  const mockUser = {
    id: '123',
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
    is_internal: true,
    is_active: true,
    internal_profile: {
      employee_id: 'EMP001',
      title: 'Senior Recruiter',
      department: {
        id: 'dept-1',
        name: 'Engineering',
      },
      roles: [
        {
          id: 'role-1',
          name: 'Recruiter',
          permissions: ['applications.view_application', 'candidates.view_candidate'],
        },
      ],
    },
  }

  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks()
    global.fetch = jest.fn()
  })

  describe('getSession', () => {
    it('should return null when no session cookie exists', async () => {
      mockCookies.mockReturnValue({
        get: jest.fn().mockReturnValue(undefined),
        set: jest.fn(),
        delete: jest.fn(),
        getAll: jest.fn(),
      } as any)

      const session = await getSession()

      expect(session).toBeNull()
    })

    it('should return session when valid cookie exists', async () => {
      mockCookies.mockReturnValue({
        get: jest.fn().mockReturnValue({ value: 'valid-session-token' }),
        set: jest.fn(),
        delete: jest.fn(),
        getAll: jest.fn(),
      } as any)

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      })

      const session = await getSession()

      expect(session).not.toBeNull()
      expect(session?.user.email).toBe('test@example.com')
      expect(session?.permissions).toEqual([
        'applications.view_application',
        'candidates.view_candidate',
      ])
      expect(session?.accessToken).toBe('valid-session-token')
    })

    it('should return null when API returns error', async () => {
      mockCookies.mockReturnValue({
        get: jest.fn().mockReturnValue({ value: 'invalid-token' }),
        set: jest.fn(),
        delete: jest.fn(),
        getAll: jest.fn(),
      } as any)

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
      })

      const session = await getSession()

      expect(session).toBeNull()
    })

    it('should extract permissions from multiple roles', async () => {
      const userWithMultipleRoles = {
        ...mockUser,
        internal_profile: {
          ...mockUser.internal_profile,
          roles: [
            {
              id: 'role-1',
              name: 'Recruiter',
              permissions: ['applications.view_application'],
            },
            {
              id: 'role-2',
              name: 'Admin',
              permissions: ['users.manage_users', 'settings.change_settings'],
            },
          ],
        },
      }

      mockCookies.mockReturnValue({
        get: jest.fn().mockReturnValue({ value: 'valid-token' }),
        set: jest.fn(),
        delete: jest.fn(),
        getAll: jest.fn(),
      } as any)

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => userWithMultipleRoles,
      })

      const session = await getSession()

      expect(session?.permissions).toEqual([
        'applications.view_application',
        'users.manage_users',
        'settings.change_settings',
      ])
    })
  })

  describe('requireAuth', () => {
    it('should return session for authenticated user', async () => {
      mockCookies.mockReturnValue({
        get: jest.fn().mockReturnValue({ value: 'valid-token' }),
        set: jest.fn(),
        delete: jest.fn(),
        getAll: jest.fn(),
      } as any)

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      })

      const session = await requireAuth()

      expect(session).not.toBeNull()
      expect(session.user.id).toBe('123')
      expect(mockRedirect).not.toHaveBeenCalled()
    })

    it('should redirect to login when not authenticated', async () => {
      mockCookies.mockReturnValue({
        get: jest.fn().mockReturnValue(undefined),
        set: jest.fn(),
        delete: jest.fn(),
        getAll: jest.fn(),
      } as any)

      mockRedirect.mockImplementation(() => {
        throw new Error('NEXT_REDIRECT')
      })

      await expect(requireAuth()).rejects.toThrow('NEXT_REDIRECT')
      expect(mockRedirect).toHaveBeenCalledWith('/login')
    })
  })

  describe('requireInternalUser', () => {
    it('should return session for internal user', async () => {
      mockCookies.mockReturnValue({
        get: jest.fn().mockReturnValue({ value: 'valid-token' }),
        set: jest.fn(),
        delete: jest.fn(),
        getAll: jest.fn(),
      } as any)

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      })

      const session = await requireInternalUser()

      expect(session).not.toBeNull()
      expect(session.user.is_internal).toBe(true)
    })

    it('should redirect when user is not internal', async () => {
      const externalUser = {
        ...mockUser,
        is_internal: false,
        internal_profile: undefined,
      }

      mockCookies.mockReturnValue({
        get: jest.fn().mockReturnValue({ value: 'valid-token' }),
        set: jest.fn(),
        delete: jest.fn(),
        getAll: jest.fn(),
      } as any)

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => externalUser,
      })

      mockRedirect.mockImplementation(() => {
        throw new Error('NEXT_REDIRECT')
      })

      await expect(requireInternalUser()).rejects.toThrow('NEXT_REDIRECT')
      expect(mockRedirect).toHaveBeenCalledWith('/login')
    })
  })
})
