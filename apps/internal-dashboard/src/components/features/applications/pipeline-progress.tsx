'use client'

import { Check, X } from 'lucide-react'

const PIPELINE_STAGES = [
  { key: 'applied', label: 'Applied' },
  { key: 'screening', label: 'Screening' },
  { key: 'interview', label: 'Interview' },
  { key: 'offer', label: 'Offer' },
  { key: 'hired', label: 'Hired' },
]

const TERMINAL_NEGATIVE = ['rejected', 'withdrawn']

interface PipelineProgressStepperProps {
  currentStatus: string
  rejectedAt?: string | null
  withdrawnAt?: string | null
}

export function PipelineProgressStepper({
  currentStatus,
  rejectedAt,
  withdrawnAt,
}: PipelineProgressStepperProps) {
  const isTerminalNegative = TERMINAL_NEGATIVE.includes(currentStatus)
  const currentIndex = PIPELINE_STAGES.findIndex((s) => s.key === currentStatus)
  // For rejected/withdrawn, find the last active stage from events or default to 0
  const activeIndex = isTerminalNegative ? -1 : currentIndex

  return (
    <div className="rounded-lg border bg-card p-4">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-4">
        Pipeline Progress
      </p>
      <div className="flex items-start">
        {PIPELINE_STAGES.map((stage, index) => {
          const isCompleted = activeIndex > index
          const isActive = activeIndex === index
          const isUpcoming = activeIndex < index && !isTerminalNegative

          return (
            <div key={stage.key} className="flex-1 flex flex-col items-center relative">
              {/* Connector line - left side */}
              {index > 0 && (
                <div
                  className={`absolute top-4 right-1/2 h-0.5 w-full -translate-y-1/2 ${
                    isCompleted || isActive ? 'bg-green-500' : 'bg-muted'
                  }`}
                  style={{ right: '50%', left: '-50%' }}
                />
              )}

              {/* Step circle */}
              <div
                className={`relative z-10 flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all ${
                  isCompleted
                    ? 'bg-green-500 border-green-500 text-white'
                    : isActive
                    ? 'bg-background border-primary ring-4 ring-primary/20 text-primary'
                    : isTerminalNegative && index <= Math.max(0, currentIndex)
                    ? 'bg-green-500 border-green-500 text-white'
                    : 'bg-background border-muted text-muted-foreground'
                }`}
              >
                {isCompleted || (isTerminalNegative && index < PIPELINE_STAGES.length) ? (
                  <Check className="h-4 w-4" strokeWidth={2.5} />
                ) : isActive ? (
                  <div className="h-2.5 w-2.5 rounded-full bg-primary" />
                ) : (
                  <div className="h-2 w-2 rounded-full bg-current opacity-30" />
                )}
              </div>

              {/* Stage label */}
              <p
                className={`mt-2 text-xs text-center leading-tight ${
                  isActive
                    ? 'text-primary font-semibold'
                    : isCompleted
                    ? 'text-green-600 font-medium'
                    : 'text-muted-foreground'
                }`}
              >
                {stage.label}
              </p>
            </div>
          )
        })}

        {/* Terminal negative state */}
        {isTerminalNegative && (
          <>
            {/* Connector to terminal */}
            <div className="flex-1 flex flex-col items-center relative">
              <div
                className="absolute top-4 h-0.5 w-full -translate-y-1/2 bg-red-200"
                style={{ right: '50%', left: '-50%' }}
              />
              <div className="relative z-10 flex h-8 w-8 items-center justify-center rounded-full bg-red-100 border-2 border-red-400 text-red-600">
                <X className="h-4 w-4" strokeWidth={2.5} />
              </div>
              <p className="mt-2 text-xs text-center text-red-600 font-semibold capitalize">
                {currentStatus === 'rejected' ? 'Rejected' : 'Withdrawn'}
              </p>
              {(rejectedAt || withdrawnAt) && (
                <p className="text-xs text-muted-foreground text-center">
                  {new Date((rejectedAt ?? withdrawnAt)!).toLocaleDateString()}
                </p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
