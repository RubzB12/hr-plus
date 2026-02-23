'use client'

import { useEffect, useState } from 'react'

export interface CompareJob {
  slug: string
  title: string
  department: string
  location: string
}

const STORAGE_KEY = 'compare_jobs'
const MAX_COMPARE = 3

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

interface CompareButtonProps {
  job: CompareJob
}

export function CompareButton({ job }: CompareButtonProps) {
  const [isSelected, setIsSelected] = useState(false)
  const [atMax, setAtMax] = useState(false)
  const [showTooltip, setShowTooltip] = useState(false)

  useEffect(() => {
    function sync() {
      const jobs = readCompareJobs()
      setIsSelected(jobs.some(j => j.slug === job.slug))
      setAtMax(jobs.length >= MAX_COMPARE)
    }
    sync()
    window.addEventListener('compare-jobs-updated', sync)
    return () => window.removeEventListener('compare-jobs-updated', sync)
  }, [job.slug])

  function toggle() {
    const jobs = readCompareJobs()
    if (isSelected) {
      writeCompareJobs(jobs.filter(j => j.slug !== job.slug))
    } else {
      if (jobs.length >= MAX_COMPARE) {
        setShowTooltip(true)
        setTimeout(() => setShowTooltip(false), 2000)
        return
      }
      writeCompareJobs([...jobs, job])
    }
  }

  return (
    <span className="relative inline-flex items-center">
      <button
        type="button"
        onClick={toggle}
        className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors ${
          isSelected
            ? 'bg-primary/10 text-primary'
            : 'bg-muted text-muted-foreground hover:text-foreground hover:bg-muted/80'
        }`}
        aria-pressed={isSelected}
      >
        <svg className="h-3 w-3" fill={isSelected ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
        </svg>
        {isSelected ? 'Added' : 'Compare'}
      </button>
      {showTooltip && (
        <span className="absolute bottom-full left-1/2 mb-1.5 -translate-x-1/2 whitespace-nowrap rounded bg-foreground px-2 py-1 text-xs text-background">
          Max {MAX_COMPARE} jobs
        </span>
      )}
    </span>
  )
}
