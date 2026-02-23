'use client'

import { useState } from 'react'

const STAGE_DESCRIPTIONS: Record<string, string> = {
  Applied: 'Your application has been received and is currently under review by the recruiting team.',
  Screening: 'A recruiter is reviewing your qualifications and may reach out to schedule a screening call.',
  'Phone Screen': 'You have been selected for an initial phone or video call with a recruiter.',
  Interview: 'You have been selected to interview with the hiring team. Check your email for scheduling details.',
  Assessment: 'You have been asked to complete a skills assessment or take-home task.',
  Offer: 'Congratulations! The team is preparing an offer for you. Keep an eye on your email.',
  Hired: 'Welcome aboard! You have been selected for this role.',
  Rejected: 'Unfortunately, the team has decided not to move forward with your application at this time.',
  Withdrawn: 'You have withdrawn your application for this position.',
}

interface StageDescriptionTooltipProps {
  stageName: string
  stageDescription?: string
}

export function StageDescriptionTooltip({ stageName, stageDescription }: StageDescriptionTooltipProps) {
  const [isOpen, setIsOpen] = useState(false)
  const description = stageDescription || STAGE_DESCRIPTIONS[stageName]

  if (!description) return null

  return (
    <span className="relative inline-flex items-center">
      <button
        type="button"
        aria-label={`What is the ${stageName} stage?`}
        onClick={() => setIsOpen(prev => !prev)}
        onBlur={() => setIsOpen(false)}
        className="ml-1.5 flex h-4 w-4 items-center justify-center rounded-full text-muted-foreground hover:text-foreground focus:outline-none"
      >
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>
      {isOpen && (
        <span className="absolute left-6 top-0 z-50 w-64 rounded-lg border border-border bg-popover p-3 text-xs text-popover-foreground shadow-lg">
          <span className="mb-1 block font-semibold">{stageName}</span>
          {description}
        </span>
      )}
    </span>
  )
}
