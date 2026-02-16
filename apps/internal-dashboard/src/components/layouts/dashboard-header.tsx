import { SidebarTrigger } from '@/components/ui/sidebar'
import { UserNav } from './user-nav'
import { getSession } from '@/lib/auth'

export async function DashboardHeader() {
  const session = await getSession()

  return (
    <header className="flex h-14 items-center justify-between border-b px-6">
      <SidebarTrigger />
      {session && <UserNav user={session.user} />}
    </header>
  )
}
