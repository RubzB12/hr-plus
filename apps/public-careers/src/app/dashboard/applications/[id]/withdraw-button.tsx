'use client'

import { useActionState, useState } from 'react'
import { withdrawAction, type WithdrawState } from './actions'

const initialState: WithdrawState = { success: false }

export function WithdrawButton({ applicationId }: { applicationId: string }) {
  const [confirming, setConfirming] = useState(false)
  const [state, formAction, isPending] = useActionState(
    withdrawAction,
    initialState
  )

  if (state.success) {
    return (
      <p className="text-sm text-green-700">
        {state.message}
      </p>
    )
  }

  if (!confirming) {
    return (
      <button
        type="button"
        onClick={() => setConfirming(true)}
        className="rounded-lg border border-red-200 px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50"
      >
        Withdraw application
      </button>
    )
  }

  return (
    <div>
      {state.message && (
        <p className="mb-3 text-sm text-red-600">{state.message}</p>
      )}
      <p className="mb-3 text-sm font-medium text-red-600">
        Are you sure you want to withdraw?
      </p>
      <form action={formAction} className="flex gap-3">
        <input type="hidden" name="applicationId" value={applicationId} />
        <button
          type="submit"
          disabled={isPending}
          className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 disabled:opacity-50"
        >
          {isPending ? 'Withdrawing...' : 'Yes, withdraw'}
        </button>
        <button
          type="button"
          onClick={() => setConfirming(false)}
          className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted"
        >
          Cancel
        </button>
      </form>
    </div>
  )
}
