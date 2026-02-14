import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getJobBySlug, getSimilarJobs } from '@/lib/dal'
import type { PublicJobDetail, PublicJob } from '@/types/api'

interface JobDetailPageProps {
  params: Promise<{ slug: string }>
}

function formatSalary(job: PublicJobDetail): string {
  if (!job.salary_min && !job.salary_max) return ''
  const currency = job.salary_currency ?? 'USD'
  const fmt = (v: string) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    }).format(Number(v))

  if (job.salary_min && job.salary_max)
    return `${fmt(job.salary_min)} - ${fmt(job.salary_max)}`
  if (job.salary_min) return `From ${fmt(job.salary_min)}`
  return `Up to ${fmt(job.salary_max!)}`
}

function formatRemotePolicy(policy: string): string {
  const labels: Record<string, string> = {
    onsite: 'On-site',
    remote: 'Remote',
    hybrid: 'Hybrid',
  }
  return labels[policy] ?? policy
}

export async function generateMetadata({
  params,
}: JobDetailPageProps): Promise<Metadata> {
  const { slug } = await params

  try {
    const job: PublicJobDetail = await getJobBySlug(slug)
    const salary = formatSalary(job)
    const description = `${job.title} at HR-Plus - ${job.department}, ${job.location_city ?? job.location_name}. ${salary ? salary + '. ' : ''}Apply now.`

    return {
      title: job.title,
      description,
      openGraph: {
        title: `${job.title} | HR-Plus Careers`,
        description,
        type: 'website',
      },
    }
  } catch {
    return { title: 'Job Not Found' }
  }
}

function JobPostingJsonLd({ job }: { job: PublicJobDetail }) {
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'JobPosting',
    title: job.title,
    description: job.description,
    datePosted: job.published_at,
    employmentType: job.employment_type?.toUpperCase().replace(' ', '_'),
    jobLocationType: job.remote_policy === 'remote' ? 'TELECOMMUTE' : undefined,
    hiringOrganization: {
      '@type': 'Organization',
      name: 'HR-Plus',
      sameAs: process.env.NEXT_PUBLIC_SITE_URL ?? 'https://careers.hrplus.com',
    },
    jobLocation: {
      '@type': 'Place',
      address: {
        '@type': 'PostalAddress',
        addressLocality: job.location_city ?? undefined,
        addressCountry: job.location_country ?? undefined,
      },
    },
    baseSalary:
      job.salary_min || job.salary_max
        ? {
            '@type': 'MonetaryAmount',
            currency: job.salary_currency ?? 'USD',
            value: {
              '@type': 'QuantitativeValue',
              minValue: job.salary_min ? Number(job.salary_min) : undefined,
              maxValue: job.salary_max ? Number(job.salary_max) : undefined,
              unitText: 'YEAR',
            },
          }
        : undefined,
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
    />
  )
}

export default async function JobDetailPage({ params }: JobDetailPageProps) {
  const { slug } = await params

  let job: PublicJobDetail
  try {
    job = await getJobBySlug(slug)
  } catch {
    notFound()
  }

  let similarJobs: PublicJob[] = []
  try {
    const response = await getSimilarJobs(job.id)
    similarJobs = Array.isArray(response) ? response : response.results ?? []
  } catch {
    // Graceful degradation
  }

  const salary = formatSalary(job)

  return (
    <>
      <JobPostingJsonLd job={job} />

      <section className="bg-muted py-10">
        <div className="mx-auto max-w-7xl px-6">
          <Link
            href="/jobs"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            &larr; Back to all positions
          </Link>
          <h1 className="mt-4 text-3xl font-bold">{job.title}</h1>
          <p className="mt-2 text-muted-foreground">{job.department}</p>

          <div className="mt-4 flex flex-wrap gap-3 text-sm">
            <span className="inline-flex items-center rounded-full bg-background px-3 py-1 border border-border">
              {job.location_city
                ? `${job.location_city}, ${job.location_country}`
                : job.location_name}
            </span>
            <span className="inline-flex items-center rounded-full bg-background px-3 py-1 border border-border">
              {job.employment_type}
            </span>
            <span className="inline-flex items-center rounded-full bg-background px-3 py-1 border border-border">
              {formatRemotePolicy(job.remote_policy)}
            </span>
            {job.level && (
              <span className="inline-flex items-center rounded-full bg-background px-3 py-1 border border-border">
                {job.level}
              </span>
            )}
            {salary && (
              <span className="inline-flex items-center rounded-full bg-primary/10 px-3 py-1 font-medium text-primary">
                {salary}
              </span>
            )}
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-6 py-10 lg:flex lg:gap-12">
        {/* Main content */}
        <article className="flex-1">
          {/* Description */}
          <section>
            <h2 className="text-xl font-semibold">About This Role</h2>
            <div
              className="prose prose-neutral mt-4 max-w-none text-foreground"
              dangerouslySetInnerHTML={{ __html: job.description }}
            />
          </section>

          {/* Required qualifications */}
          {job.requirements_required.length > 0 && (
            <section className="mt-10">
              <h2 className="text-xl font-semibold">Requirements</h2>
              <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-muted-foreground">
                {job.requirements_required.map((req, i) => (
                  <li key={i}>{req}</li>
                ))}
              </ul>
            </section>
          )}

          {/* Preferred qualifications */}
          {job.requirements_preferred.length > 0 && (
            <section className="mt-10">
              <h2 className="text-xl font-semibold">Nice to Have</h2>
              <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-muted-foreground">
                {job.requirements_preferred.map((req, i) => (
                  <li key={i}>{req}</li>
                ))}
              </ul>
            </section>
          )}

          {/* Apply CTA */}
          <div className="mt-12 rounded-lg border border-border bg-muted p-6 text-center">
            <h2 className="text-lg font-semibold">Interested in this role?</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Submit your application and our team will review it shortly.
            </p>
            <a
              href={`/apply/${job.slug}`}
              className="mt-4 inline-block rounded-lg bg-primary px-8 py-3 text-sm font-medium text-white transition-colors hover:bg-primary-dark"
            >
              Apply Now
            </a>
          </div>
        </article>

        {/* Sidebar: Similar jobs */}
        {similarJobs.length > 0 && (
          <aside className="mt-12 lg:mt-0 lg:w-80 lg:shrink-0">
            <h2 className="text-lg font-semibold">Similar Positions</h2>
            <div className="mt-4 space-y-3">
              {similarJobs.slice(0, 5).map((sj) => (
                <Link
                  key={sj.id}
                  href={`/jobs/${sj.slug}`}
                  className="block rounded-lg border border-border p-4 transition-shadow hover:shadow-md"
                >
                  <p className="font-medium">{sj.title}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {sj.department} &middot;{' '}
                    {sj.location_city ?? sj.location_name}
                  </p>
                </Link>
              ))}
            </div>
          </aside>
        )}
      </div>
    </>
  )
}
