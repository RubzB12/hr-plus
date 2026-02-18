import { notFound } from 'next/navigation'
import Link from 'next/link'
import { getApplicationDetail } from '@/lib/dal'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { ArrowLeft, Star } from 'lucide-react'

export const metadata = {
  title: 'Compare Candidates — HR-Plus',
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

interface ComparePageProps {
  searchParams: Promise<{ ids?: string; from?: string }>
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[140px_1fr] gap-3 py-3 border-b last:border-0 items-start">
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide pt-0.5">
        {label}
      </p>
      <div>{children}</div>
    </div>
  )
}

export default async function ComparePage({ searchParams }: ComparePageProps) {
  const { ids, from } = await searchParams

  if (!ids) {
    notFound()
  }

  const idList = ids
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 4) // max 4

  if (idList.length < 2) {
    return (
      <div className="space-y-4">
        <Link
          href={from ?? '/applications'}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            Select at least 2 candidates to compare.
          </CardContent>
        </Card>
      </div>
    )
  }

  // Fetch all application details in parallel; skip any that fail
  const results = await Promise.allSettled(
    idList.map((id) => getApplicationDetail(id))
  )

  const applications = results
    .filter((r): r is PromiseFulfilledResult<any> => r.status === 'fulfilled')
    .map((r) => r.value)

  if (applications.length < 2) {
    notFound()
  }

  const colCount = applications.length
  const gridCols: Record<number, string> = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href={from ?? '/applications'}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Candidate Comparison</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Comparing {applications.length} candidates side by side
          </p>
        </div>
      </div>

      {/* Comparison grid */}
      <div className={`grid gap-4 ${gridCols[colCount] ?? 'grid-cols-2'}`}>
        {applications.map((app) => (
          <Card key={app.id} className="overflow-hidden">
            <CardHeader className="pb-3 border-b bg-muted/30">
              <div className="space-y-1">
                <div className="flex items-start justify-between gap-2">
                  <Link
                    href={`/applications/${app.id}`}
                    className="font-semibold text-base hover:text-primary transition-colors leading-tight"
                  >
                    {app.candidate_name}
                  </Link>
                  {app.is_starred && (
                    <Star className="h-4 w-4 text-yellow-500 fill-yellow-500 shrink-0 mt-0.5" />
                  )}
                </div>
                <p className="text-xs text-muted-foreground truncate">{app.candidate_email}</p>
                <Badge variant={statusVariant[app.status] ?? 'secondary'} className="mt-1">
                  {statusLabel[app.status] ?? app.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <Row label="Position">
                <p className="text-sm font-medium">{app.requisition_title}</p>
                <p className="text-xs text-muted-foreground">{app.requisition_id_display}</p>
              </Row>

              <Row label="Stage">
                <p className="text-sm">{app.current_stage_name ?? 'No stage'}</p>
              </Row>

              <Row label="Department">
                <p className="text-sm">{app.department}</p>
              </Row>

              <Row label="Applied">
                <p className="text-sm">{new Date(app.applied_at).toLocaleDateString()}</p>
              </Row>

              <Row label="Source">
                <p className="text-sm capitalize">{app.source}</p>
              </Row>

              <Row label="Tags">
                {app.tags.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {app.tags.map((tag: { id: string; name: string; color: string }) => (
                      <Badge
                        key={tag.id}
                        variant="outline"
                        className="text-xs"
                        style={{ borderColor: tag.color, color: tag.color }}
                      >
                        {tag.name}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">—</p>
                )}
              </Row>

              <Row label="Cover Letter">
                {app.cover_letter ? (
                  <p className="text-sm text-muted-foreground line-clamp-4 whitespace-pre-wrap">
                    {app.cover_letter.slice(0, 300)}
                    {app.cover_letter.length > 300 ? '…' : ''}
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground">No cover letter</p>
                )}
              </Row>

              <div className="pt-3">
                <Link
                  href={`/applications/${app.id}`}
                  className="text-xs text-primary hover:underline"
                >
                  View full application →
                </Link>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
