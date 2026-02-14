import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getSession } from '@/lib/auth'
import { getJobBySlug } from '@/lib/dal'
import type { PublicJobDetail } from '@/types/api'
import { ApplyForm } from './apply-form'

interface ApplyPageProps {
  params: Promise<{ jobId: string }>
}

export async function generateMetadata({
  params,
}: ApplyPageProps): Promise<Metadata> {
  const { jobId } = await params
  try {
    const job: PublicJobDetail = await getJobBySlug(jobId)
    return {
      title: `Apply - ${job.title}`,
      description: `Apply for ${job.title} at HR-Plus.`,
    }
  } catch {
    return { title: 'Apply' }
  }
}

export default async function ApplyPage({ params }: ApplyPageProps) {
  const { jobId } = await params

  const session = await getSession()
  if (!session) {
    redirect(`/login?next=/apply/${jobId}`)
  }

  let job: PublicJobDetail
  try {
    job = await getJobBySlug(jobId)
  } catch {
    redirect('/jobs')
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold">Apply for {job.title}</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {job.department} &middot;{' '}
        {job.location_city
          ? `${job.location_city}, ${job.location_country}`
          : job.location_name}
      </p>
      <div className="mt-8">
        <ApplyForm
          job={job}
          userName={`${session.user.first_name} ${session.user.last_name}`}
          userEmail={session.user.email}
        />
      </div>
    </div>
  )
}
