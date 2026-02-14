import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getPipelineBoard, getRequisitionDetail } from '@/lib/dal'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export const metadata = {
  title: 'Pipeline Board — HR-Plus',
}

interface PipelineApplication {
  id: string
  application_id: string
  candidate_name: string
  candidate_email: string
  status: string
  current_stage_name: string | null
  is_starred: boolean
  applied_at: string
}

interface PipelineStage {
  id: string
  name: string
  order: number
  stage_type: string
  application_count: number
  applications: PipelineApplication[]
}

interface RequisitionDetail {
  id: string
  requisition_id: string
  title: string
  status: string
}

const stageTypeVariant: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  sourced: 'outline',
  applied: 'outline',
  screening: 'secondary',
  interview: 'default',
  offer: 'default',
  hired: 'default',
  rejected: 'destructive',
}

export default async function PipelineBoardPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params

  let requisition: RequisitionDetail
  let stages: PipelineStage[]

  try {
    ;[requisition, stages] = await Promise.all([
      getRequisitionDetail(id),
      getPipelineBoard(id),
    ])
  } catch {
    notFound()
  }

  const totalApplications = stages.reduce(
    (sum, stage) => sum + stage.application_count,
    0
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild>
              <Link href={`/requisitions/${id}`}>Back</Link>
            </Button>
            <h2 className="text-lg font-semibold">{requisition.title}</h2>
            <Badge variant="outline">{requisition.requisition_id}</Badge>
          </div>
          <p className="ml-14 text-sm text-muted-foreground">
            Pipeline Board &middot; {totalApplications} application{totalApplications !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {stages.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No pipeline stages configured for this requisition.
          </CardContent>
        </Card>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {stages.map((stage) => (
            <div key={stage.id} className="w-72 flex-shrink-0">
              <Card className="h-full">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">
                      {stage.name}
                    </CardTitle>
                    <Badge variant={stageTypeVariant[stage.stage_type] ?? 'secondary'}>
                      {stage.application_count}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  {stage.applications.length === 0 ? (
                    <p className="py-4 text-center text-xs text-muted-foreground">
                      No candidates
                    </p>
                  ) : (
                    stage.applications.map((app) => (
                      <Link
                        key={app.id}
                        href={`/applications/${app.id}`}
                        className="block rounded-md border p-3 transition-colors hover:bg-muted/50"
                      >
                        <div className="flex items-start justify-between">
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium">
                              {app.candidate_name}
                            </p>
                            <p className="truncate text-xs text-muted-foreground">
                              {app.candidate_email}
                            </p>
                          </div>
                          {app.is_starred && (
                            <span className="ml-2 text-yellow-500" title="Starred">
                              &#9733;
                            </span>
                          )}
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">
                          Applied {new Date(app.applied_at).toLocaleDateString()}
                        </p>
                      </Link>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
