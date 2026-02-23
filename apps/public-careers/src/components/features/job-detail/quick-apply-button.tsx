'use client'

import { useState, useTransition } from 'react'
import Link from 'next/link'
import { quickApplyAction } from '@/app/actions/quick-apply'

interface Props {
  requisitionId: string
  jobTitle: string
  profileCompleteness: number
  hasScreeningQuestions: boolean
  hasApplied: boolean
  isLoggedIn: boolean
}

export function QuickApplyButton({
  requisitionId,
  jobTitle,
  profileCompleteness,
  hasScreeningQuestions,
  hasApplied,
  isLoggedIn,
}: Props) {
  const [isPending, startTransition] = useTransition()
  const [isOpen, setIsOpen] = useState(false)
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null)

  // Only show for logged-in candidates with 80%+ profile and no screening questions
  if (!isLoggedIn || hasScreeningQuestions || profileCompleteness < 80 || hasApplied) {
    return null
  }

  const handleConfirm = () => {
    startTransition(async () => {
      const res = await quickApplyAction(requisitionId)
      setResult({ success: res.success, message: res.message ?? '' })
      if (res.success) {
        // Keep modal open to show success
      }
    })
  }

  if (result?.success) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-2.5 text-sm text-green-700">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5 shrink-0">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
        </svg>
        Applied! <Link href="/dashboard/applications" className="font-medium underline">View application</Link>
      </div>
    )
  }

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="flex-1 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100 sm:flex-none sm:px-6"
      >
        Quick Apply
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-gray-900">Confirm Quick Apply</h2>
            <p className="mt-2 text-sm text-gray-600">
              Apply to <strong>{jobTitle}</strong> using your saved profile? Your current resume and work history will be submitted.
            </p>

            {result?.message && !result.success && (
              <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {result.message}
              </div>
            )}

            <div className="mt-5 flex gap-3">
              <button
                onClick={handleConfirm}
                disabled={isPending}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
              >
                {isPending ? 'Submitting…' : 'Confirm & Apply'}
              </button>
              <button
                onClick={() => { setIsOpen(false); setResult(null) }}
                disabled={isPending}
                className="flex-1 rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-60"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
