import 'server-only'

import { getSession, type Session } from '@/lib/auth/session'

export async function requirePermission(permission: string): Promise<Session> {
  const session = await getSession()

  if (!session?.user) {
    throw new Error('Unauthorized')
  }

  if (!session.permissions?.includes(permission)) {
    throw new Error(`Forbidden: Missing permission '${permission}'`)
  }

  return session
}

export async function hasPermission(permission: string): Promise<boolean> {
  const session = await getSession()
  return session?.permissions?.includes(permission) ?? false
}
