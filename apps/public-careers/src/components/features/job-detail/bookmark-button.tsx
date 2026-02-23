'use client'

import { useOptimistic, useTransition } from 'react'
import Link from 'next/link'
import { saveJobAction, unsaveJobAction } from '@/app/dashboard/saved-jobs/actions'

interface Props {
  requisitionId: string
  initialSavedJobId: string | null
  isLoggedIn: boolean
  jobSlug: string
}

export function BookmarkButton({ requisitionId, initialSavedJobId, isLoggedIn, jobSlug }: Props) {
  const [isPending, startTransition] = useTransition()
  const [savedJobId, setOptimisticSavedJobId] = useOptimistic(initialSavedJobId)

  if (!isLoggedIn) {
    return (
      <Link
        href={`/login?next=/jobs/${jobSlug}`}
        title="Save job"
        className="inline-flex items-center justify-center rounded-lg border border-gray-200 p-2 text-gray-400 transition-colors hover:border-gray-300 hover:text-gray-600"
      >
        <BookmarkIcon filled={false} />
      </Link>
    )
  }

  const isSaved = savedJobId !== null

  const handleToggle = () => {
    startTransition(async () => {
      if (isSaved) {
        setOptimisticSavedJobId(null)
        await unsaveJobAction(savedJobId!)
      } else {
        setOptimisticSavedJobId('optimistic')
        const result = await saveJobAction(requisitionId)
        if (result.savedJobId) {
          setOptimisticSavedJobId(result.savedJobId)
        }
      }
    })
  }

  return (
    <button
      onClick={handleToggle}
      disabled={isPending}
      title={isSaved ? 'Remove from saved jobs' : 'Save job'}
      aria-label={isSaved ? 'Remove from saved jobs' : 'Save job'}
      className={`inline-flex items-center justify-center rounded-lg border p-2 transition-colors disabled:opacity-50 ${
        isSaved
          ? 'border-blue-200 bg-blue-50 text-blue-600 hover:bg-blue-100'
          : 'border-gray-200 text-gray-400 hover:border-gray-300 hover:text-gray-600'
      }`}
    >
      <BookmarkIcon filled={isSaved} />
    </button>
  )
}

function BookmarkIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill={filled ? 'currentColor' : 'none'}
      stroke="currentColor"
      strokeWidth={filled ? 0 : 1.5}
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z"
      />
    </svg>
  )
}
