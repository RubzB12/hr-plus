import Link from 'next/link'
import { getRequisitions } from '@/lib/dal'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export const metadata = {
  title: 'Requisitions — HR-Plus',
}

interface Requisition {
  id: string
  requisition_id: string
  title: string
  status: string
  department: { id: string; name: string }
  location: { id: string; name: string; city: string }
  hiring_manager: { id: string; user: { first_name: string; last_name: string } }
  recruiter: { id: string; user: { first_name: string; last_name: string } }
  employment_type: string
  headcount: number
  filled_count: number
  created_at: string
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

export default async function RequisitionsPage() {
  let data: { results: Requisition[]; count: number } = { results: [], count: 0 }

  try {
    data = await getRequisitions()
  } catch {
    // API not available yet — show empty state
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Requisitions</h2>
        <Button asChild>
          <Link href="/requisitions/new">Create Requisition</Link>
        </Button>
      </div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Title</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Department</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Hiring Manager</TableHead>
              <TableHead>Headcount</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.results.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center text-muted-foreground">
                  No requisitions found. Create your first requisition to get started.
                </TableCell>
              </TableRow>
            ) : (
              data.results.map((req) => (
                <TableRow key={req.id}>
                  <TableCell>
                    <Link href={`/requisitions/${req.id}`} className="font-medium text-primary hover:underline">
                      {req.requisition_id}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Link href={`/requisitions/${req.id}`} className="hover:underline">
                      {req.title}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant={statusVariant[req.status] ?? 'secondary'}>
                      {statusLabel[req.status] ?? req.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{req.department?.name}</TableCell>
                  <TableCell>{req.location?.city}</TableCell>
                  <TableCell>
                    {req.hiring_manager?.user?.first_name} {req.hiring_manager?.user?.last_name}
                  </TableCell>
                  <TableCell>{req.filled_count}/{req.headcount}</TableCell>
                  <TableCell>{new Date(req.created_at).toLocaleDateString()}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
