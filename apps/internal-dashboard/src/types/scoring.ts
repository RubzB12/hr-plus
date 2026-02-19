export interface CriterionBreakdownItem {
  criterion_id: string
  criterion_type: 'skill' | 'experience_years' | 'education' | 'job_title'
  value: string
  weight: number
  is_required: boolean
  factor: number
  earned: number
  detail: string
}

export interface ScorecardBreakdownItem {
  scorecard_id: string
  interviewer_name: string
  normalized_score: number
  criterion_ratings: {
    criterion_name: string
    rating: number
    weight: number
  }[]
  source: 'criterion_ratings' | 'overall_rating'
}

export interface AssessmentBreakdownItem {
  assessment_id: string
  template_name: string
  score: number
}

export interface CandidateScore {
  id: string
  profile_score: number | null
  interview_score: number | null
  assessment_score: number | null
  final_score: number | null
  profile_breakdown: { items: CriterionBreakdownItem[] }
  interview_breakdown: { scorecards: ScorecardBreakdownItem[] }
  assessment_breakdown: { assessments: AssessmentBreakdownItem[] }
  meets_required_criteria: boolean
  scored_at: string
  scoring_version: string
}
