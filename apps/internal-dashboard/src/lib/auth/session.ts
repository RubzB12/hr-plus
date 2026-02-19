import 'server-only'

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

const API_URL = process.env.DJANGO_API_URL

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  is_internal: boolean
  is_active: boolean
  internal_profile?: {
    employee_id: string
    title: string
    department: {
      id: string
      name: string
    } | null
    roles: Array<{
      id: string
      name: string
      permissions: string[]
    }>
  }
}

export interface SessionUser {
  id: string
  email: string
  first_name: string
  last_name: string
  permissions: string[]
}

export interface Session {
  user: User
  accessToken: string
  permissions: string[]
}

export async function getSession(): Promise<Session | null> {
  const cookieStore = await cookies()
  const sessionCookie = cookieStore.get('internal_session')

  if (!sessionCookie) {
    return null
  }

  try {
    const res = await fetch(`${API_URL}/api/v1/auth/me/`, {
      headers: {
        'Content-Type': 'application/json',
        Cookie: `sessionid=${sessionCookie.value}`,
      },
      cache: 'no-store',
    })

    if (!res.ok) return null
    const user = await res.json()

    // Extract permissions from roles
    const permissions =
      user.internal_profile?.roles?.flatMap((role: any) => role.permissions || []) || []

    return {
      user,
      accessToken: sessionCookie.value,
      permissions,
    }
  } catch {
    return null
  }
}

export async function requireAuth(): Promise<Session> {
  const session = await getSession()
  if (!session?.user?.id) {
    redirect('/login')
  }
  return session
}

export async function requireInternalUser(): Promise<Session> {
  const session = await requireAuth()

  if (!session.user.is_internal) {
    redirect('/login')
  }

  return session
}

export async function hasAnyPermission(permissions: string[]): Promise<boolean> {
  const session = await getSession()
  if (!session) return false

  return permissions.some((permission) => session.permissions.includes(permission))
}

export async function hasAllPermissions(permissions: string[]): Promise<boolean> {
  const session = await getSession()
  if (!session) return false

  return permissions.every((permission) => session.permissions.includes(permission))
}
