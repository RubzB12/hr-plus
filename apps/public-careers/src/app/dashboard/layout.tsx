import { redirect } from 'next/navigation'
import { cookies } from 'next/headers'
import { getSession } from '@/lib/auth'
import { getUnreadNotificationCount, getNotifications } from '@/lib/dal'
import { DashboardLayoutClient } from './layout-client'
import type { CandidateNotification } from '@/types/api'

export default async function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const session = await getSession()

  if (!session) {
    const cookieStore = await cookies()
    // If a stale session cookie exists (e.g. internal user session leaked into
    // the public site), route through the logout endpoint to delete it before
    // landing on the login page. Otherwise a plain redirect to /login is enough.
    if (cookieStore.has('session')) {
      redirect('/api/auth/logout')
    }
    redirect('/login')
  }

  const user = session.user

  let unreadCount = 0
  let notifications: CandidateNotification[] = []
  try {
    const [countResult, notifResult] = await Promise.allSettled([
      getUnreadNotificationCount(),
      getNotifications(),
    ])
    if (countResult.status === 'fulfilled') unreadCount = countResult.value
    if (notifResult.status === 'fulfilled') notifications = notifResult.value
  } catch {
    // Graceful degradation — notifications are non-critical
  }

  return (
    <DashboardLayoutClient user={user} unreadCount={unreadCount} notifications={notifications}>
      {children}
    </DashboardLayoutClient>
  )
}
