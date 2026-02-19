import { redirect } from 'next/navigation'
import { cookies } from 'next/headers'
import { getSession } from '@/lib/auth'
import { DashboardLayoutClient } from './layout-client'

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

  return <DashboardLayoutClient user={user}>{children}</DashboardLayoutClient>
}
