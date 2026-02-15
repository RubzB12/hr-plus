import { redirect } from 'next/navigation'
import { getSession } from '@/lib/auth'
import { DashboardLayoutClient } from './layout-client'

export default async function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const session = await getSession()

  if (!session) {
    redirect('/login')
  }

  const user = session.user

  return <DashboardLayoutClient user={user}>{children}</DashboardLayoutClient>
}
