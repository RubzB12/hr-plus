'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { submitScorecard } from '@/app/(dashboard)/interviews/[id]/actions'

interface ScorecardFormProps {
  interviewId: string
}

const RECOMMENDATIONS = [
  { value: 'strong_hire', label: 'Strong Hire', color: 'text-green-700' },
  { value: 'hire', label: 'Hire', color: 'text-green-600' },
  { value: 'no_hire', label: 'No Hire', color: 'text-red-600' },
  { value: 'strong_no_hire', label: 'Strong No Hire', color: 'text-red-700' },
]

export function ScorecardForm({ interviewId }: ScorecardFormProps) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const [formData, setFormData] = useState({
    overall_rating: '',
    recommendation: '',
    strengths: '',
    concerns: '',
    notes: '',
  })

  const handleSubmit = async (e: React.FormEvent, isDraft: boolean) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const submitFormData = new FormData()
      if (formData.overall_rating) {
        submitFormData.append('overall_rating', formData.overall_rating)
      }
      if (formData.recommendation) {
        submitFormData.append('recommendation', formData.recommendation)
      }
      submitFormData.append('strengths', formData.strengths)
      submitFormData.append('concerns', formData.concerns)
      submitFormData.append('notes', formData.notes)
      submitFormData.append('is_draft', String(isDraft))

      const result = await submitScorecard(interviewId, submitFormData)

      if (result.success) {
        setSuccess(true)
        if (!isDraft) {
          // If submitted (not draft), refresh the page to show other scorecards
          router.refresh()
        }
      } else {
        setError(result.error || 'Failed to submit scorecard')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to submit scorecard')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-700">
        ✓ Scorecard submitted successfully! Thank you for your feedback.
      </div>
    )
  }

  return (
    <form className="space-y-6">
      {/* Overall Rating */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Overall Rating (1-5)</label>
        <div className="flex gap-2">
          {[1, 2, 3, 4, 5].map((rating) => (
            <button
              key={rating}
              type="button"
              onClick={() => setFormData({ ...formData, overall_rating: String(rating) })}
              className={`h-12 w-12 rounded-full border-2 font-bold transition-all ${
                formData.overall_rating === String(rating)
                  ? 'border-primary bg-primary text-primary-foreground scale-110'
                  : 'border-muted hover:border-primary/50'
              }`}
            >
              {rating}
            </button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">
          1 = Poor, 3 = Average, 5 = Excellent
        </p>
      </div>

      {/* Recommendation */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Hiring Recommendation</label>
        <div className="grid grid-cols-2 gap-2">
          {RECOMMENDATIONS.map((rec) => (
            <button
              key={rec.value}
              type="button"
              onClick={() => setFormData({ ...formData, recommendation: rec.value })}
              className={`rounded-lg border-2 p-3 text-sm font-medium transition-all ${
                formData.recommendation === rec.value
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:bg-muted/50'
              }`}
            >
              <span className={formData.recommendation === rec.value ? rec.color : ''}>
                {rec.label}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Strengths */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Strengths</label>
        <textarea
          rows={4}
          placeholder="What did the candidate do well? What impressed you?"
          value={formData.strengths}
          onChange={(e) => setFormData({ ...formData, strengths: e.target.value })}
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        />
      </div>

      {/* Concerns */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Concerns</label>
        <textarea
          rows={4}
          placeholder="Any concerns or areas for improvement?"
          value={formData.concerns}
          onChange={(e) => setFormData({ ...formData, concerns: e.target.value })}
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        />
      </div>

      {/* Additional Notes */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Additional Notes</label>
        <textarea
          rows={4}
          placeholder="Any other observations or comments..."
          value={formData.notes}
          onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        />
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-4">
        <Button
          type="button"
          onClick={(e) => handleSubmit(e, true)}
          variant="outline"
          disabled={loading}
        >
          Save as Draft
        </Button>
        <Button
          type="button"
          onClick={(e) => handleSubmit(e, false)}
          disabled={loading}
          className="flex-1 md:flex-initial"
        >
          {loading ? 'Submitting...' : 'Submit Scorecard'}
        </Button>
      </div>

      <p className="text-xs text-muted-foreground">
        Note: Once submitted, you'll be able to view other interviewers' scorecards.
      </p>
    </form>
  )
}
