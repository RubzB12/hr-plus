import { getRecruiterDashboard } from '@/lib/dal'
import {
  Users,
  Briefcase,
  ClipboardCheck,
  Calendar,
  AlertCircle,
  FileCheck
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

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
    },
    {
      title: 'Active Candidates',
      value: data.active_candidates,
      icon: Users,
      description: 'Last 30 days',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'Pending Scorecards',
      value: data.pending_scorecards,
      icon: ClipboardCheck,
      description: 'Awaiting submission',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
    {
      title: 'Upcoming Interviews',
      value: data.upcoming_interviews,
      icon: Calendar,
      description: 'Next 7 days',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      title: 'Pending Approvals',
      value: data.pending_approvals,
      icon: FileCheck,
      description: 'Requiring your approval',
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
    },
    {
      title: 'Overdue Actions',
      value: data.overdue_actions,
      icon: AlertCircle,
      description: 'Needs attention',
      color: 'text-red-600',
      bgColor: 'bg-red-50',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Welcome back! Here's an overview of your hiring activity.
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {metrics.map((metric) => {
          const Icon = metric.icon
          return (
            <Card key={metric.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {metric.title}
                </CardTitle>
                <div className={`rounded-full p-2 ${metric.bgColor}`}>
                  <Icon className={`h-4 w-4 ${metric.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metric.value}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {metric.description}
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Upcoming Interviews Section */}
      {data.upcoming_interviews_list && data.upcoming_interviews_list.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Interviews</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.upcoming_interviews_list.map((interview: any, index: number) => (
                <div
                  key={interview.id || index}
                  className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0"
                >
                  <div className="space-y-1">
                    <p className="text-sm font-medium leading-none">
                      {interview.candidate_name || 'Candidate Interview'}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {interview.requisition_title || 'Position TBD'}
                    </p>
                  </div>
                  <div className="text-sm text-muted-foreground text-right">
                    <p>{interview.scheduled_date || 'Date TBD'}</p>
                    <p>{interview.scheduled_time || ''}</p>
                  </div>
                </div>
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
            <a
              href="/requisitions"
              className="flex flex-col items-center justify-center rounded-lg border border-border bg-background p-6 text-center transition-colors hover:bg-muted"
            >
              <Briefcase className="h-8 w-8 text-muted-foreground mb-2" />
              <span className="text-sm font-medium">View Requisitions</span>
            </a>
            <a
              href="/candidates"
              className="flex flex-col items-center justify-center rounded-lg border border-border bg-background p-6 text-center transition-colors hover:bg-muted"
            >
              <Users className="h-8 w-8 text-muted-foreground mb-2" />
              <span className="text-sm font-medium">Search Candidates</span>
            </a>
            <a
              href="/interviews"
              className="flex flex-col items-center justify-center rounded-lg border border-border bg-background p-6 text-center transition-colors hover:bg-muted"
            >
              <Calendar className="h-8 w-8 text-muted-foreground mb-2" />
              <span className="text-sm font-medium">Schedule Interview</span>
            </a>
            <a
              href="/analytics"
              className="flex flex-col items-center justify-center rounded-lg border border-border bg-background p-6 text-center transition-colors hover:bg-muted"
            >
              <ClipboardCheck className="h-8 w-8 text-muted-foreground mb-2" />
              <span className="text-sm font-medium">View Analytics</span>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
