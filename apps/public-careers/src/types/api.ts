export interface PublicJob {
  id: string
  title: string
  slug: string
  department: string
  location_name: string
  location_city: string
  location_country: string
  employment_type: string
  remote_policy: string
  salary_min: string | null
  salary_max: string | null
  salary_currency: string
  level: string
  published_at: string
}

export interface PublicJobDetail extends PublicJob {
  team: string | null
  description: string
  requirements_required: string[]
  requirements_preferred: string[]
  screening_questions: unknown[]
}

export interface JobCategory {
  department__id: string
  department__name: string
  job_count: number
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface CandidateApplication {
  id: string
  application_id: string
  requisition_title: string
  department: string
  status: string
  current_stage_name: string | null
  applied_at: string
}

export interface ApplicationEvent {
  id: string
  event_type: string
  actor_name: string
  from_stage_name: string | null
  to_stage_name: string | null
  metadata: Record<string, unknown>
  created_at: string
}

export interface CandidateApplicationDetail extends CandidateApplication {
  location: string
  cover_letter: string
  screening_responses: Record<string, string>
  withdrawn_at: string | null
  events: ApplicationEvent[]
}

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  is_internal: boolean
  date_joined: string
}

export interface WorkExperience {
  id: string
  company_name: string
  title: string
  start_date: string
  end_date: string | null
  is_current: boolean
  description: string
  created_at: string
  updated_at: string
}

export interface Education {
  id: string
  institution: string
  degree: string
  field_of_study: string
  start_date: string
  end_date: string | null
  gpa: string | null
  created_at: string
  updated_at: string
}

export interface Skill {
  id: string
  name: string
  proficiency: 'beginner' | 'intermediate' | 'advanced' | 'expert' | ''
  years_experience: number | null
}

export interface ProfileCompletionItem {
  field: string
  label: string
}

export interface ProfileMissingItem extends ProfileCompletionItem {
  priority: 'critical' | 'high' | 'medium' | 'low'
  action: string
}

export interface ProfileCompletionDetails {
  percentage: number
  total_items: number
  completed_count: number
  missing_count: number
  completed_items: ProfileCompletionItem[]
  missing_items: ProfileMissingItem[]
}

export interface CandidateProfile {
  id: string
  user: User
  phone: string
  location_city: string
  location_country: string
  work_authorization: string
  resume_file: string | null
  resume_parsed: Record<string, any> | null
  linkedin_url: string
  portfolio_url: string
  preferred_salary_min: string | null
  preferred_salary_max: string | null
  preferred_job_types: string[]
  profile_completeness: number
  source: string
  completeness: number
  completion_details: ProfileCompletionDetails
  experiences: WorkExperience[]
  education: Education[]
  skills: Skill[]
  created_at: string
  updated_at: string
}

export interface UserProfile {
  id: string
  email: string
  first_name: string
  last_name: string
  candidate_profile: {
    phone: string
    location_city: string
    location_country: string
    work_authorization: string
    linkedin_url: string
    portfolio_url: string
    profile_completeness: number
  }
}

export interface SearchParams {
  keywords?: string
  search?: string
  department?: string
  location?: string
  location_city?: string
  location_country?: string
  employment_type?: string
  remote_policy?: string
  level?: string
  salary_min?: number
  salary_max?: number
}

export interface SavedSearch {
  id: string
  name: string
  search_params: SearchParams
  alert_frequency: 'instant' | 'daily' | 'weekly' | 'never'
  is_active: boolean
  match_count: number
  last_notified_at: string | null
  created_at: string
  updated_at: string
}

export interface JobAlert {
  id: string
  saved_search: string
  saved_search_name: string
  requisition: string
  requisition_title: string
  requisition_slug: string
  sent_at: string
  was_clicked: boolean
  was_applied: boolean
}

export interface FacetOption {
  id?: string
  name?: string
  value?: string
  count: number
}

export interface JobFacets {
  departments: FacetOption[]
  locations: FacetOption[]
  employment_types: FacetOption[]
  remote_policies: FacetOption[]
  levels: FacetOption[]
}

export interface RecommendedJob extends PublicJob {
  match_score: number
  match_reasons: string[]
}

export interface JobRecommendationsResponse {
  count: number
  recommendations: RecommendedJob[]
}

export interface CandidateAnalyticsOverview {
  total_applications: number
  active_applications: number
  offers_received: number
  success_rate: number
  offer_rate: number
  profile_completion: number
}

export interface TimelineDataPoint {
  month: string
  applications: number
}

export interface RecentActivity {
  applications_last_30_days: number
  avg_days_in_process: number
}

export interface InterviewStats {
  total: number
  completed: number
  upcoming: number
}

export interface StatusBreakdown {
  status: string
  label: string
  count: number
  percentage: number
}

export interface Insight {
  type: 'success' | 'warning' | 'info' | 'tip'
  title: string
  message: string
  action: string | null
  action_link: string | null
}

export interface CandidateAnalyticsResponse {
  overview: CandidateAnalyticsOverview
  timeline: TimelineDataPoint[]
  recent_activity: RecentActivity
  interviews: InterviewStats
  status_breakdown: StatusBreakdown[]
  insights: Insight[]
}
