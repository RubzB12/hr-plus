import 'server-only'

import { getSession } from '@/lib/auth/session'

export async function requirePermission(permission: string) {
  const session = await getSession()

  if (!session?.user) {
    throw new Error('Unauthorized')
  }

  if (!session.user.permissions?.includes(permission)) {
    throw new Error('Forbidden: Insufficient permissions')
  }

  return session.user
}

export async function hasPermission(permission: string): Promise<boolean> {
  const session = await getSession()
  return session?.user?.permissions?.includes(permission) ?? false
}
