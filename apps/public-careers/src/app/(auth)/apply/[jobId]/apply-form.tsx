'use client'

import { useActionState, useState } from 'react'
import { applyAction, type ApplyState } from './actions'
import type { PublicJobDetail } from '@/types/api'
import { COVER_LETTER_TEMPLATES, type TemplateName } from './cover-letter-templates'

const initialState: ApplyState = { success: false }

interface ScreeningQuestion {
  id: string
  question: string
  required?: boolean
}

interface ApplyFormProps {
  job: PublicJobDetail
  userName: string
  userEmail: string
}

export function ApplyForm({ job, userName, userEmail }: ApplyFormProps) {
  const [state, formAction, isPending] = useActionState(applyAction, initialState)
  const [step, setStep] = useState(0)
  const [coverLetter, setCoverLetter] = useState('')
  const [screeningAnswers, setScreeningAnswers] = useState<Record<string, string>>({})

  const questions = (job.screening_questions ?? []) as ScreeningQuestion[]
  const hasQuestions = questions.length > 0

  // Steps: 0=Review Info, 1=Screening (if has questions), 2=Cover Letter, 3=Submit
  const steps = ['Review Info']
  if (hasQuestions) steps.push('Screening Questions')
  steps.push('Cover Letter', 'Review & Submit')

  const totalSteps = steps.length
  const isLastStep = step === totalSteps - 1

  function handleScreeningChange(questionId: string, value: string) {
    setScreeningAnswers((prev) => ({ ...prev, [questionId]: value }))
  }

  function nextStep() {
    if (step < totalSteps - 1) setStep(step + 1)
  }

  function prevStep() {
    if (step > 0) setStep(step - 1)
  }

  // Map step index to content type
  function getStepType(idx: number): string {
    return steps[idx]
  }

  const currentStepType = getStepType(step)

  return (
    <div>
      {/* Progress indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
          {steps.map((label, i) => (
            <span
              key={label}
              className={`${i <= step ? 'text-primary font-medium' : ''}`}
            >
              {label}
            </span>
          ))}
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-border">
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${((step + 1) / totalSteps) * 100}%` }}
          />
        </div>
      </div>

      {state.message && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {state.message}
        </div>
      )}

      {/* Step: Review Info */}
      {currentStepType === 'Review Info' && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Confirm your information</h2>
          <div className="rounded-lg border border-border p-4 space-y-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Name
              </p>
              <p className="text-sm">{userName}</p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Email
              </p>
              <p className="text-sm">{userEmail}</p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Position
              </p>
              <p className="text-sm">{job.title}</p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Department
              </p>
              <p className="text-sm">{job.department}</p>
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Make sure your profile is up to date before applying.
          </p>
        </div>
      )}

      {/* Step: Screening Questions */}
      {currentStepType === 'Screening Questions' && (
        <div className="space-y-5">
          <h2 className="text-lg font-semibold">Screening Questions</h2>
          {questions.map((q) => (
            <div key={q.id}>
              <label htmlFor={`q-${q.id}`} className="block text-sm font-medium">
                {q.question}
                {q.required && <span className="text-red-500 ml-1">*</span>}
              </label>
              <textarea
                id={`q-${q.id}`}
                rows={3}
                required={q.required}
                value={screeningAnswers[q.question] ?? ''}
                onChange={(e) =>
                  handleScreeningChange(q.question, e.target.value)
                }
                className="mt-1.5 block w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
              />
            </div>
          ))}
        </div>
      )}

      {/* Step: Cover Letter */}
      {currentStepType === 'Cover Letter' && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Cover Letter</h2>
          <p className="text-sm text-muted-foreground">
            Optional. Tell us why you are a great fit for this role.
          </p>

          {/* Template buttons */}
          <div>
            <p className="mb-2 text-xs font-medium text-muted-foreground">Start from a template:</p>
            <div className="flex flex-wrap gap-2">
              {(Object.keys(COVER_LETTER_TEMPLATES) as TemplateName[]).map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() =>
                    setCoverLetter(
                      COVER_LETTER_TEMPLATES[key](job.title, 'HR-Plus')
                    )
                  }
                  className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium capitalize transition-colors hover:bg-muted hover:border-primary/40"
                >
                  {key}
                </button>
              ))}
            </div>
          </div>

          <textarea
            rows={8}
            value={coverLetter}
            onChange={(e) => setCoverLetter(e.target.value)}
            maxLength={5000}
            placeholder="Write your cover letter here, or pick a template above..."
            className="block w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-1 focus:ring-primary"
          />
          <p className="text-xs text-muted-foreground text-right">
            {coverLetter.length} / 5000
          </p>
        </div>
      )}

      {/* Step: Review & Submit */}
      {currentStepType === 'Review & Submit' && (
        <div className="space-y-5">
          <h2 className="text-lg font-semibold">Review your application</h2>

          <div className="rounded-lg border border-border divide-y divide-border">
            <div className="p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Applicant
              </p>
              <p className="mt-1 text-sm">
                {userName} ({userEmail})
              </p>
            </div>
            <div className="p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Position
              </p>
              <p className="mt-1 text-sm">
                {job.title} - {job.department}
              </p>
            </div>
            {coverLetter && (
              <div className="p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Cover Letter
                </p>
                <p className="mt-1 text-sm whitespace-pre-wrap line-clamp-4">
                  {coverLetter}
                </p>
              </div>
            )}
            {Object.keys(screeningAnswers).length > 0 && (
              <div className="p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Screening Responses
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {Object.keys(screeningAnswers).length} question(s) answered
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="mt-8 flex items-center justify-between">
        {step > 0 ? (
          <button
            type="button"
            onClick={prevStep}
            className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted"
          >
            Back
          </button>
        ) : (
          <div />
        )}

        {isLastStep ? (
          <form action={formAction}>
            <input type="hidden" name="requisition_id" value={job.id} />
            <input type="hidden" name="cover_letter" value={coverLetter} />
            <input
              type="hidden"
              name="screening_responses"
              value={JSON.stringify(screeningAnswers)}
            />
            <button
              type="submit"
              disabled={isPending}
              className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-dark disabled:opacity-50"
            >
              {isPending ? 'Submitting...' : 'Submit application'}
            </button>
          </form>
        ) : (
          <button
            type="button"
            onClick={nextStep}
            className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-dark"
          >
            Continue
          </button>
        )}
      </div>
    </div>
  )
}
