import Link from 'next/link'
import { redirect } from 'next/navigation'
import { getSession } from '@/lib/auth'
import { LogoutButton } from './logout-button'

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

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <div className="lg:flex lg:gap-10">
        {/* Sidebar navigation */}
        <aside className="mb-8 lg:mb-0 lg:w-56 lg:shrink-0">
          <div className="mb-6">
            <p className="text-sm font-medium">
              {user.first_name} {user.last_name}
            </p>
            <p className="text-xs text-muted-foreground">{user.email}</p>
          </div>
          <nav className="flex gap-2 lg:flex-col">
            <Link
              href="/dashboard/applications"
              className="rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              Applications
            </Link>
            <Link
              href="/dashboard/profile"
              className="rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              Profile
            </Link>
            <Link
              href="/jobs"
              className="rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              Browse Jobs
            </Link>
            <LogoutButton />
          </nav>
        </aside>

        {/* Main content */}
        <div className="flex-1 min-w-0">{children}</div>
      </div>
    </div>
  )
}
