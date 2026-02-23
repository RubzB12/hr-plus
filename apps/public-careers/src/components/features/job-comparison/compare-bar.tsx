'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { CompareJob } from './compare-button'

const STORAGE_KEY = 'compare_jobs'

function readCompareJobs(): CompareJob[] {
  if (typeof window === 'undefined') return []
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]')
  } catch {
    return []
  }
}

function writeCompareJobs(jobs: CompareJob[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(jobs))
  window.dispatchEvent(new CustomEvent('compare-jobs-updated'))
}

export function CompareBar() {
  const [jobs, setJobs] = useState<CompareJob[]>([])
  const router = useRouter()

  useEffect(() => {
    function sync() {
      setJobs(readCompareJobs())
    }
    sync()
    window.addEventListener('compare-jobs-updated', sync)
    return () => window.removeEventListener('compare-jobs-updated', sync)
  }, [])

  if (jobs.length < 2) return null

  function remove(slug: string) {
    writeCompareJobs(jobs.filter(j => j.slug !== slug))
  }

  function clearAll() {
    writeCompareJobs([])
  }

  function compare() {
    const slugs = jobs.map(j => j.slug).join(',')
    router.push(`/jobs/compare?jobs=${slugs}`)
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background/95 px-6 py-3 shadow-lg backdrop-blur-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-muted-foreground">Comparing:</span>
          {jobs.map(job => (
            <span
              key={job.slug}
              className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary"
            >
              {job.title}
              <button
                type="button"
                onClick={() => remove(job.slug)}
                aria-label={`Remove ${job.title}`}
                className="ml-0.5 rounded-full hover:text-primary/70"
              >
                <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          ))}
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <button
            type="button"
            onClick={clearAll}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            Clear all
          </button>
          <button
            type="button"
            onClick={compare}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary/90"
          >
            Compare ({jobs.length})
          </button>
        </div>
      </div>
    </div>
  )
}
