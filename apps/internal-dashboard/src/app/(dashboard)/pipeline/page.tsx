import { PipelineOverviewClient } from './pipeline-overview-client'

export const metadata = {
  title: 'Pipeline Overview — HR-Plus',
}

export default function PipelineOverviewPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Pipeline Overview</h1>
        <p className="text-muted-foreground mt-2">
          Aggregated view of all active hiring pipelines
        </p>
      </div>
      <PipelineOverviewClient />
    </div>
  )
}
