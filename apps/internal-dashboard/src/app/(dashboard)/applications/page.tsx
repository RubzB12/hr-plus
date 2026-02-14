import Link from 'next/link'
import { getApplications } from '@/lib/dal'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'

export const metadata = {
  title: 'Applications — HR-Plus',
}

interface ApplicationListItem {
  id: string
  application_id: string
  candidate_name: string
  candidate_email: string
  requisition_title: string
  status: string
  current_stage_name: string | null
  source: string
  is_starred: boolean
  applied_at: string
}

const statusVariant: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  applied: 'default',
  screening: 'outline',
  interview: 'outline',
  offer: 'default',
  hired: 'secondary',
  rejected: 'destructive',
  withdrawn: 'secondary',
}

const statusLabel: Record<string, string> = {
  applied: 'Applied',
  screening: 'Screening',
  interview: 'Interview',
  offer: 'Offer',
  hired: 'Hired',
  rejected: 'Rejected',
  withdrawn: 'Withdrawn',
}

export default async function ApplicationsPage() {
  let data: { results: ApplicationListItem[]; count: number } = { results: [], count: 0 }

  try {
    data = await getApplications()
  } catch {
    // API not available yet — show empty state
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Applications</h2>
        <p className="text-sm text-muted-foreground">{data.count} total</p>
      </div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Application ID</TableHead>
              <TableHead>Candidate</TableHead>
              <TableHead>Requisition</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Stage</TableHead>
              <TableHead>Source</TableHead>
              <TableHead className="text-center">Starred</TableHead>
              <TableHead>Applied Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.results.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center text-muted-foreground">
                  No applications found.
                </TableCell>
              </TableRow>
            ) : (
              data.results.map((app) => (
                <TableRow key={app.id}>
                  <TableCell>
                    <Link
                      href={`/applications/${app.id}`}
                      className="font-medium text-primary hover:underline"
                    >
                      {app.application_id}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="font-medium">{app.candidate_name}</p>
                      <p className="text-xs text-muted-foreground">{app.candidate_email}</p>
                    </div>
                  </TableCell>
                  <TableCell>{app.requisition_title}</TableCell>
                  <TableCell>
                    <Badge variant={statusVariant[app.status] ?? 'secondary'}>
                      {statusLabel[app.status] ?? app.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{app.current_stage_name ?? '—'}</TableCell>
                  <TableCell className="capitalize">{app.source}</TableCell>
                  <TableCell className="text-center">
                    {app.is_starred ? (
                      <span className="text-yellow-500" title="Starred">&#9733;</span>
                    ) : (
                      <span className="text-muted-foreground" title="Not starred">&#9734;</span>
                    )}
                  </TableCell>
                  <TableCell>{new Date(app.applied_at).toLocaleDateString()}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
