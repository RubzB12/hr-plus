'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { Bell, Calendar, ClipboardCheck, AlertCircle, FileCheck, ArrowRight, Loader2 } from 'lucide-react'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'

interface UpcomingInterview {
  id?: string
  candidate_name?: string
  requisition_title?: string
  scheduled_date?: string
  scheduled_time?: string
}

interface DashboardData {
  pending_scorecards: number
  upcoming_interviews: number
  upcoming_interviews_list: UpcomingInterview[]
  pending_approvals: number
  overdue_actions: number
}

function NotificationSection({
  icon: Icon,
  title,
  count,
  href,
  children,
}: {
  icon: React.ElementType
  title: string
  count: number
  href: string
  children?: React.ReactNode
}) {
  if (count === 0 && !children) return null

  return (
    <div className="py-3 border-b last:border-0">
      <div className="flex items-center justify-between mb-2 px-4">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-muted-foreground" />
          <p className="text-sm font-medium">{title}</p>
          {count > 0 && (
            <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-primary text-[10px] font-semibold text-primary-foreground px-1">
              {count > 99 ? '99+' : count}
            </span>
          )}
        </div>
        <Link
          href={href}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-primary transition-colors"
        >
          View all
          <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
      {children}
    </div>
  )
}

export function NotificationsPanel() {
  const [open, setOpen] = useState(false)
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/internal/analytics/dashboard/recruiter/`,
        { credentials: 'include' }
      )
      if (res.ok) {
        setData(await res.json())
      }
    } catch {
      // silently fail — notifications are non-critical
    } finally {
      setLoading(false)
    }
  }, [])

  // Fetch on first open
  useEffect(() => {
    if (open && !data) {
      fetchData()
    }
  }, [open, data, fetchData])

  const urgentCount = data
    ? (data.pending_scorecards ?? 0) + (data.overdue_actions ?? 0)
    : 0

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        title="Notifications"
        className="relative inline-flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
      >
        <Bell className="h-4 w-4" />
        {urgentCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white">
            {urgentCount > 9 ? '9+' : urgentCount}
          </span>
        )}
      </button>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="right" className="w-80 sm:w-96 p-0 flex flex-col">
          <SheetHeader className="border-b px-4 py-4">
            <SheetTitle className="flex items-center gap-2">
              <Bell className="h-4 w-4" />
              Notifications
              {urgentCount > 0 && (
                <span className="ml-auto flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-semibold text-white px-1">
                  {urgentCount > 99 ? '99+' : urgentCount}
                </span>
              )}
            </SheetTitle>
          </SheetHeader>

          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-16 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin mr-2" />
                Loading...
              </div>
            ) : !data ? (
              <div className="py-12 text-center text-sm text-muted-foreground px-4">
                Unable to load notifications. Try again later.
              </div>
            ) : urgentCount === 0 && (data.upcoming_interviews ?? 0) === 0 && (data.pending_approvals ?? 0) === 0 ? (
              <div className="py-16 text-center px-4">
                <Bell className="h-10 w-10 text-muted-foreground mx-auto mb-3 opacity-40" />
                <p className="text-sm font-medium">All caught up!</p>
                <p className="text-xs text-muted-foreground mt-1">
                  No pending actions at the moment.
                </p>
              </div>
            ) : (
              <div>
                {/* Upcoming Interviews */}
                {(data.upcoming_interviews_list?.length ?? 0) > 0 && (
                  <NotificationSection
                    icon={Calendar}
                    title="Upcoming Interviews"
                    count={data.upcoming_interviews ?? 0}
                    href="/interviews"
                  >
                    <div className="space-y-1 px-4">
                      {data.upcoming_interviews_list.slice(0, 5).map((interview, i) => (
                        <Link
                          key={interview.id ?? i}
                          href={interview.id ? `/interviews/${interview.id}` : '/interviews'}
                          onClick={() => setOpen(false)}
                          className="flex items-center justify-between rounded-md px-2 py-2 hover:bg-muted transition-colors group"
                        >
                          <div className="min-w-0">
                            <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">
                              {interview.candidate_name ?? 'Interview'}
                            </p>
                            <p className="text-xs text-muted-foreground truncate">
                              {interview.requisition_title ?? ''}
                            </p>
                          </div>
                          <div className="text-xs text-muted-foreground text-right ml-3 shrink-0">
                            <p>{interview.scheduled_date ?? ''}</p>
                            <p>{interview.scheduled_time ?? ''}</p>
                          </div>
                        </Link>
                      ))}
                    </div>
                  </NotificationSection>
                )}

                {/* Pending Scorecards */}
                {(data.pending_scorecards ?? 0) > 0 && (
                  <NotificationSection
                    icon={ClipboardCheck}
                    title="Pending Scorecards"
                    count={data.pending_scorecards}
                    href="/interviews"
                  >
                    <div className="px-4">
                      <Link
                        href="/interviews"
                        onClick={() => setOpen(false)}
                        className="flex items-center gap-2 rounded-md px-2 py-2 hover:bg-muted transition-colors"
                      >
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-orange-100 shrink-0">
                          <ClipboardCheck className="h-4 w-4 text-orange-600" />
                        </div>
                        <p className="text-sm">
                          <span className="font-medium">{data.pending_scorecards}</span> interview{data.pending_scorecards !== 1 ? 's' : ''} awaiting your scorecard
                        </p>
                      </Link>
                    </div>
                  </NotificationSection>
                )}

                {/* Overdue Actions */}
                {(data.overdue_actions ?? 0) > 0 && (
                  <NotificationSection
                    icon={AlertCircle}
                    title="Overdue Actions"
                    count={data.overdue_actions}
                    href="/applications"
                  >
                    <div className="px-4">
                      <Link
                        href="/applications"
                        onClick={() => setOpen(false)}
                        className="flex items-center gap-2 rounded-md px-2 py-2 hover:bg-muted transition-colors"
                      >
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-100 shrink-0">
                          <AlertCircle className="h-4 w-4 text-red-600" />
                        </div>
                        <p className="text-sm">
                          <span className="font-medium">{data.overdue_actions}</span> application{data.overdue_actions !== 1 ? 's' : ''} need immediate attention
                        </p>
                      </Link>
                    </div>
                  </NotificationSection>
                )}

                {/* Pending Approvals */}
                {(data.pending_approvals ?? 0) > 0 && (
                  <NotificationSection
                    icon={FileCheck}
                    title="Pending Approvals"
                    count={data.pending_approvals}
                    href="/applications"
                  >
                    <div className="px-4">
                      <Link
                        href="/applications"
                        onClick={() => setOpen(false)}
                        className="flex items-center gap-2 rounded-md px-2 py-2 hover:bg-muted transition-colors"
                      >
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 shrink-0">
                          <FileCheck className="h-4 w-4 text-indigo-600" />
                        </div>
                        <p className="text-sm">
                          <span className="font-medium">{data.pending_approvals}</span> requisition{data.pending_approvals !== 1 ? 's' : ''} awaiting approval
                        </p>
                      </Link>
                    </div>
                  </NotificationSection>
                )}
              </div>
            )}
          </div>

          {data && (
            <div className="border-t px-4 py-3">
              <button
                onClick={fetchData}
                className="text-xs text-muted-foreground hover:text-primary transition-colors"
              >
                Refresh notifications
              </button>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </>
  )
}
