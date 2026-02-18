import { getRecruiterDashboard } from '@/lib/dal'
import {
  Users,
  Briefcase,
  ClipboardCheck,
  Calendar,
  AlertCircle,
  FileCheck,
  ArrowUpRight,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Link from 'next/link'

export const metadata = {
  title: 'Dashboard — HR-Plus',
}

interface DashboardData {
  open_requisitions: number
  active_candidates: number
  pending_scorecards: number
  upcoming_interviews: number
  upcoming_interviews_list: any[]
  pending_approvals: number
  overdue_actions: number
}

export default async function DashboardPage() {
  const data: DashboardData = await getRecruiterDashboard()

  const metrics = [
    {
      title: 'Open Requisitions',
      value: data.open_requisitions,
      icon: Briefcase,
      description: 'Active job openings',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      href: '/requisitions',
    },
    {
      title: 'Active Candidates',
      value: data.active_candidates,
      icon: Users,
      description: 'Last 30 days',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      href: '/candidates',
    },
    {
      title: 'Pending Scorecards',
      value: data.pending_scorecards,
      icon: ClipboardCheck,
      description: 'Awaiting submission',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      href: '/interviews?status=pending_scorecard',
    },
    {
      title: 'Upcoming Interviews',
      value: data.upcoming_interviews,
      icon: Calendar,
      description: 'Next 7 days',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      href: '/interviews',
    },
    {
      title: 'Pending Approvals',
      value: data.pending_approvals,
      icon: FileCheck,
      description: 'Requiring your approval',
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      href: '/offers?status=pending',
    },
    {
      title: 'Overdue Actions',
      value: data.overdue_actions,
      icon: AlertCircle,
      description: 'Needs attention',
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      href: '/applications?status=screening',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Welcome back! Here&apos;s an overview of your hiring activity.
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {metrics.map((metric) => {
          const Icon = metric.icon
          return (
            <Link key={metric.title} href={metric.href} className="group block">
              <Card className="h-full transition-all hover:shadow-md hover:border-primary/30 cursor-pointer">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {metric.title}
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <div className={`rounded-full p-2 ${metric.bgColor}`}>
                      <Icon className={`h-4 w-4 ${metric.color}`} />
                    </div>
                    <ArrowUpRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metric.value}</div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {metric.description}
                  </p>
                </CardContent>
              </Card>
            </Link>
          )
        })}
      </div>

      {/* Upcoming Interviews Section */}
      {data.upcoming_interviews_list && data.upcoming_interviews_list.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Upcoming Interviews</CardTitle>
            <Link
              href="/interviews"
              className="text-sm text-muted-foreground hover:text-primary flex items-center gap-1 transition-colors"
            >
              View all
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.upcoming_interviews_list.map((interview: any, index: number) => (
                <Link
                  key={interview.id || index}
                  href={interview.id ? `/interviews/${interview.id}` : '/interviews'}
                  className="flex items-center justify-between rounded-lg px-3 py-3 border hover:bg-muted/50 hover:border-primary/30 transition-all group"
                >
                  <div className="space-y-0.5">
                    <p className="text-sm font-medium leading-none group-hover:text-primary transition-colors">
                      {interview.candidate_name || 'Candidate Interview'}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {interview.requisition_title || 'Position TBD'}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-sm text-muted-foreground text-right">
                      <p>{interview.scheduled_date || 'Date TBD'}</p>
                      <p>{interview.scheduled_time || ''}</p>
                    </div>
                    <ArrowUpRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Link
              href="/requisitions"
              className="flex flex-col items-center justify-center rounded-lg border border-border bg-background p-6 text-center transition-colors hover:bg-muted hover:border-primary/30"
            >
              <Briefcase className="h-8 w-8 text-muted-foreground mb-2" />
              <span className="text-sm font-medium">View Requisitions</span>
            </Link>
            <Link
              href="/candidates"
              className="flex flex-col items-center justify-center rounded-lg border border-border bg-background p-6 text-center transition-colors hover:bg-muted hover:border-primary/30"
            >
              <Users className="h-8 w-8 text-muted-foreground mb-2" />
              <span className="text-sm font-medium">Search Candidates</span>
            </Link>
            <Link
              href="/interviews/schedule"
              className="flex flex-col items-center justify-center rounded-lg border border-border bg-background p-6 text-center transition-colors hover:bg-muted hover:border-primary/30"
            >
              <Calendar className="h-8 w-8 text-muted-foreground mb-2" />
              <span className="text-sm font-medium">Schedule Interview</span>
            </Link>
            <Link
              href="/analytics"
              className="flex flex-col items-center justify-center rounded-lg border border-border bg-background p-6 text-center transition-colors hover:bg-muted hover:border-primary/30"
            >
              <ClipboardCheck className="h-8 w-8 text-muted-foreground mb-2" />
              <span className="text-sm font-medium">View Analytics</span>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
