import { SidebarTrigger } from '@/components/ui/sidebar'
import { UserNav } from './user-nav'
import { getSession } from '@/lib/auth'
import { SearchTrigger } from './search-trigger'
import { Breadcrumbs } from './breadcrumbs'

export async function DashboardHeader() {
  const session = await getSession()

  return (
    <header className="flex h-14 items-center justify-between border-b px-6">
      <div className="flex items-center gap-3 min-w-0">
        <SidebarTrigger className="shrink-0" />
        <Breadcrumbs />
        <SearchTrigger />
      </div>
      {session && <UserNav user={session.user} />}
    </header>
  )
}
