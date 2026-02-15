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
    <div className="min-h-screen bg-gradient-to-b from-muted/30 to-background py-12">
      <div className="mx-auto w-full max-w-3xl px-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            Job Application
          </div>
          <h1 className="mt-2 text-3xl font-bold">{job.title}</h1>
          <div className="mt-2 flex items-center gap-3 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              {job.department}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {job.location_city
                ? `${job.location_city}, ${job.location_country}`
                : job.location_name}
            </span>
          </div>
        </div>

        {/* Application Form Card */}
        <div className="rounded-xl border border-border bg-card p-8 shadow-sm">
          <ApplyForm
            job={job}
            userName={`${session.user.first_name} ${session.user.last_name}`}
            userEmail={session.user.email}
          />
        </div>

        {/* Help Text */}
        <p className="mt-6 text-center text-sm text-muted-foreground">
          Need help? Contact{' '}
          <a href="mailto:careers@hrplus.com" className="font-medium text-primary hover:underline">
            careers@hrplus.com
          </a>
        </p>
      </div>
    </div>
  )
}
