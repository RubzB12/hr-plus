import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getRequisitionDetail } from '@/lib/dal'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { RequisitionActions } from './requisition-actions'

export const metadata = {
  title: 'Requisition Detail — HR-Plus',
}

interface Approval {
  id: string
  approver: { id: string; user: { first_name: string; last_name: string } }
  order: number
  status: string
  decided_at: string | null
  comments: string
}

interface Stage {
  id: string
  name: string
  order: number
  stage_type: string
}

interface RequisitionDetail {
  id: string
  requisition_id: string
  title: string
  slug: string
  status: string
  department: { id: string; name: string }
  team: { id: string; name: string } | null
  location: { id: string; name: string; city: string; country: string }
  level: { id: string; name: string }
  hiring_manager: { id: string; user: { first_name: string; last_name: string; email: string } }
  recruiter: { id: string; user: { first_name: string; last_name: string; email: string } }
  employment_type: string
  remote_policy: string
  salary_min: string | null
  salary_max: string | null
  salary_currency: string
  description: string
  headcount: number
  filled_count: number
  target_start_date: string | null
  target_fill_date: string | null
  opened_at: string | null
  published_at: string | null
  version: number
  stages: Stage[]
  approvals: Approval[]
  created_at: string
  updated_at: string
}

const statusVariant: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  draft: 'secondary',
  pending_approval: 'outline',
  approved: 'default',
  open: 'default',
  on_hold: 'outline',
  filled: 'secondary',
  cancelled: 'destructive',
}

const statusLabel: Record<string, string> = {
  draft: 'Draft',
  pending_approval: 'Pending Approval',
  approved: 'Approved',
  open: 'Open',
  on_hold: 'On Hold',
  filled: 'Filled',
  cancelled: 'Cancelled',
}

const approvalStatusVariant: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  pending: 'outline',
  approved: 'default',
  rejected: 'destructive',
  skipped: 'secondary',
}

const employmentTypeLabel: Record<string, string> = {
  full_time: 'Full-time',
  part_time: 'Part-time',
  contract: 'Contract',
  temporary: 'Temporary',
  internship: 'Internship',
}

const remotePolicyLabel: Record<string, string> = {
  onsite: 'On-site',
  hybrid: 'Hybrid',
  remote: 'Remote',
}

export default async function RequisitionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  let requisition: RequisitionDetail

  try {
    requisition = await getRequisitionDetail(id)
  } catch {
    notFound()
  }

  const salary =
    requisition.salary_min && requisition.salary_max
      ? `${requisition.salary_currency} ${Number(requisition.salary_min).toLocaleString()} – ${Number(requisition.salary_max).toLocaleString()}`
      : requisition.salary_min
        ? `${requisition.salary_currency} ${Number(requisition.salary_min).toLocaleString()}+`
        : null

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold">{requisition.title}</h2>
            <Badge variant={statusVariant[requisition.status] ?? 'secondary'}>
              {statusLabel[requisition.status] ?? requisition.status}
            </Badge>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {requisition.requisition_id} · v{requisition.version}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" asChild>
            <Link href={`/requisitions/${requisition.id}/pipeline`}>View Pipeline</Link>
          </Button>
          <RequisitionActions requisitionId={requisition.id} status={requisition.status} />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Department</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">{requisition.department?.name}</p>
            {requisition.team && (
              <p className="text-sm text-muted-foreground">{requisition.team.name}</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Location</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">{requisition.location?.city}, {requisition.location?.country}</p>
            <p className="text-sm text-muted-foreground">
              {remotePolicyLabel[requisition.remote_policy] ?? requisition.remote_policy}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Headcount</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">{requisition.filled_count} / {requisition.headcount} filled</p>
            <p className="text-sm text-muted-foreground">
              {employmentTypeLabel[requisition.employment_type] ?? requisition.employment_type}
              {' · '}{requisition.level?.name}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Hiring Manager</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">
              {requisition.hiring_manager?.user?.first_name} {requisition.hiring_manager?.user?.last_name}
            </p>
            <p className="text-sm text-muted-foreground">{requisition.hiring_manager?.user?.email}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Recruiter</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium">
              {requisition.recruiter?.user?.first_name} {requisition.recruiter?.user?.last_name}
            </p>
            <p className="text-sm text-muted-foreground">{requisition.recruiter?.user?.email}</p>
          </CardContent>
        </Card>

        {salary && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Salary Range</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-medium">{salary}</p>
            </CardContent>
          </Card>
        )}
      </div>

      {requisition.approvals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Approval Chain</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {requisition.approvals.map((approval) => (
                <div key={approval.id} className="flex items-center justify-between rounded-lg border p-3">
                  <div className="flex items-center gap-3">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-muted text-xs font-medium">
                      {approval.order + 1}
                    </span>
                    <div>
                      <p className="font-medium">
                        {approval.approver?.user?.first_name} {approval.approver?.user?.last_name}
                      </p>
                      {approval.comments && (
                        <p className="text-sm text-muted-foreground">{approval.comments}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={approvalStatusVariant[approval.status] ?? 'secondary'}>
                      {approval.status}
                    </Badge>
                    {approval.decided_at && (
                      <span className="text-xs text-muted-foreground">
                        {new Date(approval.decided_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Pipeline Stages</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {requisition.stages.map((stage) => (
              <Badge key={stage.id} variant="outline">
                {stage.order + 1}. {stage.name}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Description</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none dark:prose-invert whitespace-pre-wrap">
            {requisition.description}
          </div>
        </CardContent>
      </Card>

      <div className="text-xs text-muted-foreground">
        Created {new Date(requisition.created_at).toLocaleString()}
        {' · '}Updated {new Date(requisition.updated_at).toLocaleString()}
        {requisition.opened_at && (
          <> · Opened {new Date(requisition.opened_at).toLocaleString()}</>
        )}
        {requisition.published_at && (
          <> · Published {new Date(requisition.published_at).toLocaleString()}</>
        )}
      </div>
    </div>
  )
}
