'use client'

import { useActionState, useState } from 'react'
import { withdrawAction, type WithdrawState } from './actions'

const WITHDRAW_REASONS = [
  'Accepted another offer',
  'Role no longer a fit',
  'Personal reasons',
  'Salary expectations',
  'Other',
]

const initialState: WithdrawState = { success: false }

export function WithdrawButton({ applicationId }: { applicationId: string }) {
  const [open, setOpen] = useState(false)
  const [selectedReason, setSelectedReason] = useState('')
  const [customReason, setCustomReason] = useState('')
  const [state, formAction, isPending] = useActionState(withdrawAction, initialState)

  if (state.success) {
    return (
      <p className="text-sm text-green-700">{state.message}</p>
    )
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-lg border border-red-200 px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50"
      >
        Withdraw application
      </button>
    )
  }

  const reasonValue = selectedReason === 'Other' ? customReason : selectedReason

  return (
    <div className="space-y-4">
      {state.message && (
        <p className="text-sm text-red-600">{state.message}</p>
      )}

      <div>
        <label htmlFor="withdraw-reason" className="block text-sm font-medium text-red-900 mb-1.5">
          Why are you withdrawing? <span className="text-red-400">(optional)</span>
        </label>
        <select
          id="withdraw-reason"
          value={selectedReason}
          onChange={e => setSelectedReason(e.target.value)}
          className="block w-full rounded-lg border border-red-200 bg-white px-3 py-2 text-sm text-gray-700 outline-none focus:border-red-400 focus:ring-1 focus:ring-red-400"
        >
          <option value="">Select a reason...</option>
          {WITHDRAW_REASONS.map(r => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </div>

      {selectedReason === 'Other' && (
        <div>
          <label htmlFor="custom-reason" className="block text-sm font-medium text-red-900 mb-1.5">
            Please specify
          </label>
          <textarea
            id="custom-reason"
            rows={2}
            maxLength={200}
            value={customReason}
            onChange={e => setCustomReason(e.target.value)}
            placeholder="Tell us more..."
            className="block w-full rounded-lg border border-red-200 bg-white px-3 py-2 text-sm text-gray-700 outline-none focus:border-red-400 focus:ring-1 focus:ring-red-400 resize-none"
          />
        </div>
      )}

      <form action={formAction} className="flex gap-3">
        <input type="hidden" name="applicationId" value={applicationId} />
        <input type="hidden" name="reason" value={reasonValue} />
        <button
          type="submit"
          disabled={isPending}
          className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 disabled:opacity-50"
        >
          {isPending ? 'Withdrawing...' : 'Confirm withdrawal'}
        </button>
        <button
          type="button"
          onClick={() => { setOpen(false); setSelectedReason(''); setCustomReason('') }}
          className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted"
        >
          Cancel
        </button>
      </form>
    </div>
  )
}
