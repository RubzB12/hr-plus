# HR-Plus — Enterprise HR Hiring Platform
## Product Requirements Document & Comprehensive Scope

---

## 1. Executive Summary

HR-Plus is a full-cycle hiring platform built for large corporations. It serves two distinct audiences through separate frontends: **external candidates** who discover jobs, apply, and track their hiring journey, and **internal staff** (recruiters, hiring managers, interviewers, HR admins, and executives) who manage requisitions, evaluate candidates, and drive hiring decisions.

The platform is built on a **Next.js** frontend (two apps: public and internal) and a **Django** backend (REST API + async task processing), designed for enterprise-grade scale, compliance, and security.

---

## 2. User Roles & Personas

### 2.1 External Users

| Role | Description |
|---|---|
| **Anonymous Visitor** | Browses job listings without an account. Can search, filter, and view job details. |
| **Candidate** | Registered user who applies to jobs, uploads documents, completes assessments, tracks application status, and communicates with recruiters. |
| **Referrer** | External person (or existing employee via a shared link) who submits a referral for a candidate. |

### 2.2 Internal Users

| Role | Description |
|---|---|
| **Recruiter** | Owns the hiring pipeline. Creates requisitions, sources candidates, manages applications, schedules interviews, extends offers. |
| **Hiring Manager** | Department lead who requests headcount, defines role requirements, reviews candidates, and makes final hiring decisions. |
| **Interviewer** | Conducts interviews and submits structured evaluations/scorecards. |
| **HR Admin** | Configures system settings, manages workflows, handles compliance, manages user accounts and permissions. |
| **Executive / Leadership** | Views hiring analytics, dashboards, headcount planning, and approves high-level requisitions. |
| **Coordinator** | Supports logistics — scheduling interviews, managing rooms/links, sending reminders. |
| **Onboarding Specialist** | Picks up after offer acceptance — manages pre-boarding tasks, document collection, and system provisioning. |

### 2.3 System Actors

| Actor | Description |
|---|---|
| **Background Job Worker** | Celery workers handling email dispatch, PDF generation, data syncs, and scheduled tasks. |
| **Notification Engine** | Dispatches emails, in-app notifications, SMS, and webhook events. |
| **Integration Broker** | Manages data flow to/from external systems (HRIS, calendar, background check vendors, etc.). |

---

## 3. System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      CDN / Edge                         │
├──────────────────────┬──────────────────────────────────┤
│  Public Next.js App  │  Internal Next.js App            │
│  (careers site)      │  (staff dashboard)               │
│  SSR + Static Gen    │  CSR + SSR hybrid                │
├──────────────────────┴──────────────────────────────────┤
│                   API Gateway / Load Balancer            │
├─────────────────────────────────────────────────────────┤
│                  Django REST API                         │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐            │
│  │ Auth &   │ │ Hiring    │ │ Comms &    │            │
│  │ RBAC     │ │ Pipeline  │ │ Notifs     │            │
│  ├──────────┤ ├───────────┤ ├────────────┤            │
│  │ Jobs &   │ │ Assess-   │ │ Analytics  │            │
│  │ Reqs     │ │ ments     │ │ & Reports  │            │
│  ├──────────┤ ├───────────┤ ├────────────┤            │
│  │ Candi-   │ │ Offers &  │ │ Integra-   │            │
│  │ dates    │ │ Onboard   │ │ tions      │            │
│  └──────────┘ └───────────┘ └────────────┘            │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis  │  Celery  │  S3/Blob Storage   │
├─────────────────────────────────────────────────────────┤
│  Elasticsearch (search)  │  WebSocket Server (realtime) │
└─────────────────────────────────────────────────────────┘
```

### 3.1 Technology Stack

| Layer | Technology |
|---|---|
| Public Frontend | Next.js 14+ (App Router), TypeScript, Tailwind CSS, React Query |
| Internal Frontend | Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui, React Query, Zustand |
| API | Django 5+, Django REST Framework, django-filter |
| Auth | Django Allauth (candidates), Django OAuth Toolkit, SAML2/OIDC (internal SSO) |
| Database | PostgreSQL 16+ with pgvector (for resume/semantic search) |
| Cache & Queue | Redis (caching + Celery broker) |
| Task Queue | Celery + Celery Beat (scheduled tasks) |
| Search | Elasticsearch 8 (job search, candidate search) |
| File Storage | S3-compatible (AWS S3, MinIO for dev) |
| Realtime | Django Channels (WebSocket for notifications, live updates) |
| Email | SMTP integration + template engine (django-templated-email) |
| PDF Generation | WeasyPrint or Puppeteer microservice |
| CI/CD | GitHub Actions, Docker, Kubernetes |
| Monitoring | Sentry (errors), Prometheus + Grafana (metrics), ELK (logs) |
| Testing | pytest (Django), Jest + Playwright (Next.js) |

---

## 4. Module Breakdown

---

### Module 1: Job Board & Career Site (Public Frontend)

**Purpose:** The public-facing careers site where candidates discover and apply to jobs.

#### 4.1.1 Features

**Job Listing & Search**
- Filterable, searchable job listings (keyword, location, department, employment type, salary range, remote/hybrid/onsite)
- Full-text search powered by Elasticsearch with typo tolerance and synonym matching
- Geo-based search with radius filtering and map view
- SEO-optimized job pages with structured data (JSON-LD for Google Jobs)
- URL structure: `/careers/jobs/[slug]` with canonical URLs
- Saved search alerts — candidates get notified when new matching jobs are posted
- Social sharing (Open Graph tags, Twitter cards)
- Job categories and department landing pages
- "Similar jobs" recommendations

**Company Branding Pages**
- Customizable company culture pages (mission, values, benefits, team spotlights)
- Department-specific pages with team descriptions and media
- Employee testimonials and video embeds
- Office location pages with maps
- Diversity & inclusion page
- Benefits and perks breakdown

**Job Detail Page**
- Rich job description with sections: overview, responsibilities, qualifications (required vs. preferred), compensation range, benefits, team info
- "Easy Apply" button (pre-fill from profile or LinkedIn)
- Application deadline and posting date
- Hiring manager or recruiter preview (optional)
- Application count indicator (e.g., "50+ applicants")
- Accessibility: WCAG 2.1 AA compliant

#### 4.1.2 User Stories

- As a visitor, I can search for jobs by keyword and location so I find relevant openings.
- As a visitor, I can filter jobs by department, type, and salary range to narrow results.
- As a visitor, I can view a detailed job posting with requirements and benefits.
- As a visitor, I can share a job posting on social media or via email.
- As a candidate, I can save a job to apply later.
- As a candidate, I can set up job alerts based on my search criteria.

#### 4.1.3 API Endpoints

```
GET    /api/v1/jobs/                     # List jobs (public, paginated, filterable)
GET    /api/v1/jobs/{slug}/              # Job detail
GET    /api/v1/jobs/search/              # Elasticsearch-powered search
GET    /api/v1/jobs/categories/          # List categories/departments
GET    /api/v1/jobs/{id}/similar/        # Similar job recommendations
POST   /api/v1/jobs/{id}/alerts/         # Create job alert subscription
GET    /api/v1/locations/                # Office locations
GET    /api/v1/company/culture/          # Culture page content (CMS-driven)
```

---

### Module 2: Candidate Portal

**Purpose:** Authenticated candidate experience — profile management, applications, and communication.

#### 4.2.1 Features

**Registration & Authentication**
- Email + password registration with email verification
- Social login (Google, LinkedIn, Apple)
- LinkedIn profile import (auto-fill name, experience, education)
- Magic link / passwordless login option
- Multi-factor authentication (optional, encouraged for sensitive actions)

**Candidate Profile**
- Personal information (name, contact, location, work authorization)
- Resume upload (PDF, DOCX) with parsed extraction into structured fields
- Resume builder (in-app, section-by-section)
- Work experience timeline
- Education history
- Skills & certifications
- Portfolio links / GitHub / personal website
- Preferred job types, locations, salary expectations
- EEO / voluntary self-identification data (optional, stored separately)
- Profile completeness indicator with prompts

**Application Flow**
- Multi-step application form (per-job, configurable by recruiter):
  - Step 1: Review & confirm profile info
  - Step 2: Job-specific screening questions (text, multiple choice, yes/no, file upload)
  - Step 3: Cover letter (optional, configurable)
  - Step 4: EEO / voluntary demographics (always optional, anonymized)
  - Step 5: Review & submit
- Draft saving — candidates can return and finish later
- Duplicate application prevention (warn if already applied)
- Application confirmation email with tracking link
- "Easy Apply" — one-click apply using saved profile (skips steps where data exists)

**Application Tracking**
- Dashboard showing all applications with real-time status
- Status stages: Applied → Screening → Interview → Assessment → Offer → Hired (configurable)
- Timeline view of all events per application (submitted, reviewed, interview scheduled, etc.)
- Document requests from recruiter (upload additional files)
- Withdrawal option with optional reason

**Interview Scheduling (Candidate Side)**
- Self-scheduling via calendar link (see available slots, pick one)
- View upcoming interviews with details (who, when, where/link, what to prepare)
- Reschedule request (within allowed window)
- Add to personal calendar (iCal, Google Calendar)
- Interview prep materials provided by recruiter

**Communication**
- In-app messaging with recruiter (threaded)
- Email notifications with in-app echo
- Notification preferences (email, SMS, push)
- Automated status update notifications

#### 4.2.2 Data Model (Core Entities)

```python
class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = EncryptedCharField(max_length=20)
    location_city = models.CharField(max_length=100)
    location_country = models.CharField(max_length=100)
    work_authorization = models.CharField(choices=WORK_AUTH_CHOICES)
    resume_file = models.FileField(upload_to='resumes/')
    resume_parsed = models.JSONField(null=True)  # Structured parsed resume data
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    preferred_salary_min = models.DecimalField(null=True)
    preferred_salary_max = models.DecimalField(null=True)
    preferred_job_types = ArrayField(models.CharField(choices=JOB_TYPE_CHOICES))
    profile_completeness = models.IntegerField(default=0)
    source = models.CharField(choices=SOURCE_CHOICES)  # How they found us
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class WorkExperience(models.Model):
    candidate = models.ForeignKey(CandidateProfile, related_name='experiences')
    company_name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True)  # null = current
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)

class Education(models.Model):
    candidate = models.ForeignKey(CandidateProfile, related_name='education')
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    gpa = models.DecimalField(null=True)

class Skill(models.Model):
    candidate = models.ForeignKey(CandidateProfile, related_name='skills')
    name = models.CharField(max_length=100)
    proficiency = models.CharField(choices=PROFICIENCY_CHOICES, blank=True)
    years_experience = models.IntegerField(null=True)
```

#### 4.2.3 API Endpoints

```
POST   /api/v1/auth/register/                  # Candidate registration
POST   /api/v1/auth/login/                      # Login (email/password)
POST   /api/v1/auth/social/{provider}/          # Social auth (Google, LinkedIn)
POST   /api/v1/auth/magic-link/                 # Passwordless login
GET    /api/v1/auth/me/                          # Current user profile

GET    /api/v1/candidates/profile/               # Get own profile
PUT    /api/v1/candidates/profile/               # Update profile
POST   /api/v1/candidates/resume/upload/         # Upload & parse resume
GET    /api/v1/candidates/resume/parsed/         # Get parsed resume data

POST   /api/v1/applications/                     # Submit application
GET    /api/v1/applications/                     # List own applications
GET    /api/v1/applications/{id}/                # Application detail + timeline
PUT    /api/v1/applications/{id}/draft/          # Save draft
POST   /api/v1/applications/{id}/withdraw/       # Withdraw application
POST   /api/v1/applications/{id}/documents/      # Upload requested document

GET    /api/v1/interviews/upcoming/              # Candidate's upcoming interviews
POST   /api/v1/interviews/{id}/schedule/         # Self-schedule from available slots
POST   /api/v1/interviews/{id}/reschedule/       # Request reschedule

GET    /api/v1/messages/                         # List conversations
GET    /api/v1/messages/{thread_id}/             # Thread detail
POST   /api/v1/messages/{thread_id}/reply/       # Send message
PUT    /api/v1/notifications/preferences/        # Update notification prefs
```

---

### Module 3: Requisition Management (Internal)

**Purpose:** The backbone of hiring — creating, approving, and managing job requisitions.

#### 4.3.1 Features

**Requisition Creation**
- Multi-step requisition form:
  - Job details (title, department, team, level, employment type)
  - Compensation (salary range, equity, bonus structure, currency)
  - Job description (rich text editor with templates)
  - Requirements (required vs. preferred qualifications)
  - Screening questions (builder with question bank)
  - Hiring team assignment (recruiter, hiring manager, interviewers)
  - Interview plan (stages, interview types, scorecards)
  - Headcount (number of openings)
  - Target dates (open date, target fill date)
  - Posting channels (internal only, external job boards, specific boards)
- Requisition templates (clone from previous or template library)
- Bulk requisition creation (e.g., seasonal hiring)
- AI-assisted job description writing (suggest improvements, check for biased language)

**Approval Workflow**
- Configurable multi-level approval chains:
  - Hiring Manager → Department Head → Finance → HR → VP (example)
- Approval rules based on: level, salary band, department, headcount
- Sequential or parallel approval paths
- Approval delegation (out-of-office)
- Automated reminders for pending approvals
- Approval audit trail
- Reject with reason → return to requester for revision

**Requisition Lifecycle**
- States: Draft → Pending Approval → Approved → Open → On Hold → Filled → Cancelled
- Reason codes for hold/cancel
- Automatic expiry (configurable, e.g., 90 days with renewal option)
- Reopen previously filled/cancelled requisitions (creates new version)
- Requisition history and versioning

**Job Board Distribution**
- Publish to internal career site
- Push to external job boards (Indeed, LinkedIn, Glassdoor, etc.) via integrations
- Social media posting (generate shareable links)
- Employee referral program link generation
- Internal-only postings (employee mobility)
- Scheduled posting (future publish date)
- Post to multiple locations simultaneously

#### 4.3.2 Data Model

```python
class Requisition(models.Model):
    requisition_id = models.CharField(max_length=20, unique=True)  # e.g., REQ-2026-001
    title = models.CharField(max_length=200)
    department = models.ForeignKey('Department')
    team = models.ForeignKey('Team', null=True)
    hiring_manager = models.ForeignKey('InternalUser', related_name='managed_reqs')
    recruiter = models.ForeignKey('InternalUser', related_name='owned_reqs')
    status = models.CharField(choices=REQ_STATUS_CHOICES)
    employment_type = models.CharField(choices=EMPLOYMENT_TYPE_CHOICES)
    level = models.ForeignKey('JobLevel')
    location = models.ForeignKey('Location')
    remote_policy = models.CharField(choices=REMOTE_CHOICES)
    salary_min = models.DecimalField()
    salary_max = models.DecimalField()
    salary_currency = models.CharField(max_length=3)
    equity_included = models.BooleanField(default=False)
    description = models.TextField()  # Rich text / HTML
    requirements_required = models.JSONField()
    requirements_preferred = models.JSONField()
    screening_questions = models.JSONField()
    headcount = models.IntegerField(default=1)
    filled_count = models.IntegerField(default=0)
    target_start_date = models.DateField(null=True)
    target_fill_date = models.DateField(null=True)
    opened_at = models.DateTimeField(null=True)
    closed_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey('InternalUser')
    created_at = models.DateTimeField(auto_now_add=True)
    version = models.IntegerField(default=1)

class RequisitionApproval(models.Model):
    requisition = models.ForeignKey(Requisition, related_name='approvals')
    approver = models.ForeignKey('InternalUser')
    order = models.IntegerField()
    status = models.CharField(choices=['pending', 'approved', 'rejected', 'skipped'])
    decided_at = models.DateTimeField(null=True)
    comments = models.TextField(blank=True)
    delegated_to = models.ForeignKey('InternalUser', null=True)

class InterviewPlan(models.Model):
    requisition = models.ForeignKey(Requisition, related_name='interview_plans')
    stage_name = models.CharField(max_length=100)
    stage_order = models.IntegerField()
    interview_type = models.CharField(choices=INTERVIEW_TYPE_CHOICES)
    duration_minutes = models.IntegerField()
    interviewer_count = models.IntegerField(default=1)
    scorecard_template = models.ForeignKey('ScorecardTemplate', null=True)
    instructions = models.TextField(blank=True)
```

#### 4.3.3 API Endpoints

```
POST   /api/v1/internal/requisitions/                    # Create requisition
GET    /api/v1/internal/requisitions/                    # List (filterable by status, dept, recruiter)
GET    /api/v1/internal/requisitions/{id}/               # Detail
PUT    /api/v1/internal/requisitions/{id}/               # Update
POST   /api/v1/internal/requisitions/{id}/submit/        # Submit for approval
POST   /api/v1/internal/requisitions/{id}/approve/       # Approve
POST   /api/v1/internal/requisitions/{id}/reject/        # Reject
POST   /api/v1/internal/requisitions/{id}/publish/       # Publish to job boards
POST   /api/v1/internal/requisitions/{id}/hold/          # Put on hold
POST   /api/v1/internal/requisitions/{id}/cancel/        # Cancel
POST   /api/v1/internal/requisitions/{id}/clone/         # Clone as new draft
GET    /api/v1/internal/requisitions/{id}/history/       # Version history

GET    /api/v1/internal/requisition-templates/           # List templates
POST   /api/v1/internal/requisition-templates/           # Create template

GET    /api/v1/internal/approvals/pending/               # My pending approvals
POST   /api/v1/internal/approvals/{id}/delegate/         # Delegate approval
```

---

### Module 4: Application & Pipeline Management (Internal)

**Purpose:** The core recruiter workspace — managing candidates through the hiring pipeline.

#### 4.4.1 Features

**Pipeline / Kanban Board**
- Drag-and-drop Kanban view per requisition showing candidates in each stage
- Configurable pipeline stages per requisition (default: Applied → Screened → Phone Screen → Interview → Assessment → Offer → Hired)
- Bulk actions (move stage, reject, send email, add tags)
- Quick filters (stage, rating, source, date range, tags)
- Sort by: application date, rating, last activity
- Candidate count per stage
- Stage duration tracking (time-in-stage metrics)

**Application Review**
- Candidate summary card (photo optional, name, headline, location, source, applied date)
- Resume viewer (in-app PDF/DOCX rendering)
- Parsed resume data alongside raw document
- Screening question responses
- AI-powered resume scoring against job requirements (configurable, optional)
- Side-by-side comparison of multiple candidates
- Candidate notes (private to reviewer)
- Shared evaluation notes (visible to hiring team)
- Activity log per application (all events, automated and manual)

**Candidate Actions**
- Advance to next stage / move to any stage
- Reject with reason (from rejection reason library) and optional personalized message
- Request additional information from candidate
- Schedule interview
- Send templated or custom email
- Add/remove tags
- Flag for review
- Transfer to another requisition
- Archive (for talent pool)

**Candidate Search & Sourcing**
- Global candidate database search (across all past and current applicants)
- Full-text search across resumes, notes, skills
- Semantic / AI-powered search ("find me senior engineers with distributed systems experience")
- Filters: skills, experience years, location, education, source, application history, tags
- Saved searches
- Talent pools (curated candidate lists for future roles)
- Source tracking (where did each candidate come from)
- Duplicate candidate detection and merge

**Referral Management**
- Employee referral portal (internal frontend)
- Referral link generation per job
- Track referral source through pipeline
- Referral bonus tracking and status
- Referral leaderboard (gamification, optional)

#### 4.4.2 Data Model

```python
class Application(models.Model):
    application_id = models.CharField(max_length=20, unique=True)
    candidate = models.ForeignKey('CandidateProfile', related_name='applications')
    requisition = models.ForeignKey('Requisition', related_name='applications')
    status = models.CharField(choices=APPLICATION_STATUS_CHOICES)
    current_stage = models.ForeignKey('PipelineStage')
    source = models.CharField(choices=SOURCE_CHOICES)
    referrer = models.ForeignKey('InternalUser', null=True, related_name='referrals')
    resume_snapshot = models.FileField()  # Snapshot at time of application
    cover_letter = models.TextField(blank=True)
    screening_responses = models.JSONField(default=dict)
    ai_score = models.FloatField(null=True)
    ai_score_breakdown = models.JSONField(null=True)
    tags = models.ManyToManyField('Tag', blank=True)
    is_starred = models.BooleanField(default=False)
    rejection_reason = models.ForeignKey('RejectionReason', null=True)
    rejected_at = models.DateTimeField(null=True)
    hired_at = models.DateTimeField(null=True)
    withdrawn_at = models.DateTimeField(null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PipelineStage(models.Model):
    requisition = models.ForeignKey('Requisition', related_name='stages')
    name = models.CharField(max_length=100)
    order = models.IntegerField()
    stage_type = models.CharField(choices=STAGE_TYPE_CHOICES)
    auto_actions = models.JSONField(default=list)  # Triggered when candidate enters stage

class ApplicationEvent(models.Model):
    application = models.ForeignKey(Application, related_name='events')
    event_type = models.CharField(choices=EVENT_TYPE_CHOICES)
    actor = models.ForeignKey('User', null=True)  # null for system events
    from_stage = models.ForeignKey(PipelineStage, null=True, related_name='+')
    to_stage = models.ForeignKey(PipelineStage, null=True, related_name='+')
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class CandidateNote(models.Model):
    application = models.ForeignKey(Application, related_name='notes')
    author = models.ForeignKey('InternalUser')
    content = models.TextField()
    is_private = models.BooleanField(default=False)
    mentions = models.ManyToManyField('InternalUser', related_name='mentioned_in_notes')
    created_at = models.DateTimeField(auto_now_add=True)

class TalentPool(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey('InternalUser')
    candidates = models.ManyToManyField('CandidateProfile')
    is_dynamic = models.BooleanField(default=False)  # Auto-populated by saved search
    search_criteria = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 4.4.3 API Endpoints

```
GET    /api/v1/internal/applications/                        # List/search applications
GET    /api/v1/internal/applications/{id}/                   # Detail with timeline
POST   /api/v1/internal/applications/{id}/advance/           # Move to next stage
POST   /api/v1/internal/applications/{id}/move/              # Move to specific stage
POST   /api/v1/internal/applications/{id}/reject/            # Reject
POST   /api/v1/internal/applications/{id}/transfer/          # Transfer to another req
POST   /api/v1/internal/applications/{id}/notes/             # Add note
GET    /api/v1/internal/applications/{id}/events/            # Event timeline

GET    /api/v1/internal/requisitions/{id}/pipeline/          # Kanban view data
POST   /api/v1/internal/applications/bulk/                   # Bulk actions

GET    /api/v1/internal/candidates/search/                   # Global candidate search
GET    /api/v1/internal/candidates/{id}/                     # Full candidate profile
GET    /api/v1/internal/candidates/{id}/applications/        # All applications by candidate
POST   /api/v1/internal/candidates/merge/                    # Merge duplicate candidates

GET    /api/v1/internal/talent-pools/                        # List talent pools
POST   /api/v1/internal/talent-pools/                        # Create pool
POST   /api/v1/internal/talent-pools/{id}/add/               # Add candidates
DELETE /api/v1/internal/talent-pools/{id}/remove/            # Remove candidates

GET    /api/v1/internal/referrals/                           # Referral dashboard
POST   /api/v1/internal/referrals/                           # Submit referral
```

---

### Module 5: Interview Management

**Purpose:** Scheduling, conducting, and evaluating interviews.

#### 4.5.1 Features

**Scheduling**
- Calendar integration (Google Calendar, Outlook/Microsoft 365)
- Interviewer availability management (sync from calendar, manual overrides)
- Auto-scheduling engine: finds optimal slots based on:
  - Interviewer availability
  - Candidate preferences (self-schedule)
  - Room/resource availability
  - Time zone handling
  - Buffer time between interviews
- Interview types: phone screen, video, onsite, panel, take-home, group
- Panel interview coordination (find time when all panelists are available)
- Interview loops / super-days (schedule multiple back-to-back interviews)
- Rescheduling and cancellation workflows
- Automated reminders (24h, 1h before interview)
- Video conferencing link auto-generation (Zoom, Teams, Google Meet)
- Room booking integration

**Scorecards & Evaluation**
- Configurable scorecard templates per interview stage
- Structured evaluation criteria (competencies, skills, values)
- Rating scale (customizable: 1-4, 1-5, strong no hire → strong hire)
- Per-criterion rating + overall recommendation
- Written feedback (required vs. optional fields)
- Feedback submission deadline enforcement
- Anti-bias features:
  - Independent feedback (can't see others' feedback until you submit yours)
  - Structured criteria reduce subjective bias
  - Optional: blind review mode (hide candidate name/photo)
- Interviewer training materials and rubrics

**Debrief**
- Debrief scheduling (auto-schedule after all interviews complete)
- Debrief dashboard: all scorecards side-by-side
- Consensus rating / hiring decision
- Debrief notes and final recommendation
- Decision options: Hire, No Hire, Hold, Move to different role

#### 4.5.2 Data Model

```python
class Interview(models.Model):
    application = models.ForeignKey('Application', related_name='interviews')
    interview_plan_stage = models.ForeignKey('InterviewPlan')
    interview_type = models.CharField(choices=INTERVIEW_TYPE_CHOICES)
    status = models.CharField(choices=['scheduled', 'completed', 'cancelled', 'no_show'])
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    timezone = models.CharField(max_length=50)
    location = models.CharField(blank=True)  # Room name or "Virtual"
    video_link = models.URLField(blank=True)
    candidate_prep_notes = models.TextField(blank=True)
    interviewer_prep_notes = models.TextField(blank=True)
    created_by = models.ForeignKey('InternalUser')
    created_at = models.DateTimeField(auto_now_add=True)

class InterviewParticipant(models.Model):
    interview = models.ForeignKey(Interview, related_name='participants')
    interviewer = models.ForeignKey('InternalUser')
    role = models.CharField(choices=['lead', 'shadow', 'observer'])
    rsvp_status = models.CharField(choices=['pending', 'accepted', 'declined', 'tentative'])

class Scorecard(models.Model):
    interview = models.ForeignKey(Interview, related_name='scorecards')
    interviewer = models.ForeignKey('InternalUser')
    overall_rating = models.IntegerField(choices=RATING_CHOICES)
    overall_recommendation = models.CharField(choices=RECOMMENDATION_CHOICES)
    strengths = models.TextField(blank=True)
    concerns = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True)
    is_draft = models.BooleanField(default=True)

class ScorecardCriterionRating(models.Model):
    scorecard = models.ForeignKey(Scorecard, related_name='criterion_ratings')
    criterion = models.ForeignKey('ScorecardCriterion')
    rating = models.IntegerField()
    comment = models.TextField(blank=True)

class ScorecardTemplate(models.Model):
    name = models.CharField(max_length=200)
    department = models.ForeignKey('Department', null=True)
    criteria = models.ManyToManyField('ScorecardCriterion', through='TemplateCriterion')
    rating_scale = models.JSONField()  # e.g., {"1": "Strong No", "2": "No", "3": "Yes", "4": "Strong Yes"}

class Debrief(models.Model):
    application = models.ForeignKey('Application', related_name='debriefs')
    scheduled_at = models.DateTimeField(null=True)
    decision = models.CharField(choices=DECISION_CHOICES, blank=True)
    notes = models.TextField(blank=True)
    decided_by = models.ForeignKey('InternalUser', null=True)
    decided_at = models.DateTimeField(null=True)
```

#### 4.5.3 API Endpoints

```
POST   /api/v1/internal/interviews/                          # Schedule interview
GET    /api/v1/internal/interviews/                          # List interviews (filterable)
GET    /api/v1/internal/interviews/{id}/                     # Detail
PUT    /api/v1/internal/interviews/{id}/                     # Update
POST   /api/v1/internal/interviews/{id}/cancel/              # Cancel
GET    /api/v1/internal/interviews/availability/             # Check interviewer availability
POST   /api/v1/internal/interviews/auto-schedule/            # Auto-schedule engine

POST   /api/v1/internal/interviews/{id}/scorecards/          # Submit scorecard
GET    /api/v1/internal/interviews/{id}/scorecards/          # View scorecards (post-submission only)
PUT    /api/v1/internal/scorecards/{id}/                     # Update draft scorecard

POST   /api/v1/internal/applications/{id}/debrief/           # Create debrief
PUT    /api/v1/internal/debriefs/{id}/                       # Record decision
GET    /api/v1/internal/debriefs/{id}/summary/               # Debrief summary with all scorecards
```

---

### Module 6: Assessment & Testing

**Purpose:** Evaluate candidates through structured assessments beyond interviews.

#### 4.6.1 Features

**Assessment Types**
- Skills assessments (coding challenges, writing samples, case studies)
- Personality / behavioral assessments (via third-party integration)
- Take-home assignments with deadline tracking
- Live coding / whiteboard sessions (integration with CoderPad, HackerRank, etc.)
- Background checks (integration with Checkr, Sterling, etc.)
- Reference checks (automated outreach + structured form)

**Assessment Management**
- Assessment library (reusable templates)
- Auto-trigger assessments at specific pipeline stages
- Candidate-facing assessment portal (instructions, submission, timer)
- Reviewer assignment and grading interface
- Scoring rubrics
- Plagiarism / integrity checks (for coding assessments)
- Results aggregation into candidate profile

**Reference Checks**
- Automated reference request emails
- Structured reference questionnaire builder
- Reference response collection and summary
- Configurable number of references required
- Reference status tracking

#### 4.6.2 API Endpoints

```
POST   /api/v1/internal/assessments/                         # Create assessment
GET    /api/v1/internal/assessments/templates/               # Assessment template library
POST   /api/v1/internal/applications/{id}/assessments/assign/ # Assign to candidate
GET    /api/v1/internal/applications/{id}/assessments/       # List assessments for application

# Candidate-facing
GET    /api/v1/assessments/{token}/                          # Get assessment details (token-based)
POST   /api/v1/assessments/{token}/submit/                   # Submit assessment

# Reference checks
POST   /api/v1/internal/applications/{id}/references/request/  # Request references
GET    /api/v1/internal/applications/{id}/references/          # View reference responses
POST   /api/v1/references/{token}/submit/                      # Reference submits response (token-based)

# Background checks
POST   /api/v1/internal/applications/{id}/background-check/    # Initiate background check
GET    /api/v1/internal/applications/{id}/background-check/    # Check status/results
```

---

### Module 7: Offer Management

**Purpose:** Create, approve, extend, and track employment offers.

#### 4.7.1 Features

**Offer Creation**
- Offer builder with fields: base salary, bonus, equity, sign-on bonus, start date, title, level, department, reporting manager, benefits summary
- Compensation benchmarking (against internal bands and market data)
- Offer letter template engine (merge fields from offer data)
- PDF offer letter generation with e-signature integration (DocuSign, Adobe Sign)
- Multi-currency support

**Offer Approval**
- Configurable approval workflow (similar to requisition approval)
- Approval rules: salary threshold triggers additional approvers
- Compensation committee review for executive hires
- Budget impact visibility

**Offer Lifecycle**
- States: Draft → Pending Approval → Approved → Sent → Viewed → Accepted → Declined → Expired → Revoked
- Offer expiration (configurable deadline)
- Candidate negotiation tracking (counter-offer log)
- Offer revision (create new version, maintain history)
- Decline reason capture
- Competing offer tracking

**Candidate-Facing Offer Experience**
- Secure offer portal (token-based access)
- Interactive offer breakdown (total compensation visualization)
- Accept / Decline / Request to Discuss buttons
- E-signature capture
- Document upload (signed offer letter, start date confirmation)

#### 4.7.2 Data Model

```python
class Offer(models.Model):
    offer_id = models.CharField(max_length=20, unique=True)
    application = models.ForeignKey('Application', related_name='offers')
    version = models.IntegerField(default=1)
    status = models.CharField(choices=OFFER_STATUS_CHOICES)
    title = models.CharField(max_length=200)
    level = models.ForeignKey('JobLevel')
    department = models.ForeignKey('Department')
    reporting_to = models.ForeignKey('InternalUser', null=True)
    base_salary = models.DecimalField()
    salary_currency = models.CharField(max_length=3)
    salary_frequency = models.CharField(choices=['annual', 'monthly', 'hourly'])
    bonus_percentage = models.DecimalField(null=True)
    bonus_target = models.DecimalField(null=True)
    equity_shares = models.IntegerField(null=True)
    equity_vesting_schedule = models.CharField(blank=True)
    sign_on_bonus = models.DecimalField(null=True)
    relocation_package = models.DecimalField(null=True)
    start_date = models.DateField()
    expiration_date = models.DateField()
    offer_letter_pdf = models.FileField(null=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('InternalUser')
    sent_at = models.DateTimeField(null=True)
    viewed_at = models.DateTimeField(null=True)
    responded_at = models.DateTimeField(null=True)
    decline_reason = models.TextField(blank=True)
    esignature_envelope_id = models.CharField(blank=True)  # DocuSign/Adobe Sign ID
    created_at = models.DateTimeField(auto_now_add=True)

class OfferNegotiationLog(models.Model):
    offer = models.ForeignKey(Offer, related_name='negotiations')
    logged_by = models.ForeignKey('InternalUser')
    candidate_request = models.TextField()
    internal_response = models.TextField(blank=True)
    outcome = models.CharField(choices=['accepted', 'counter', 'declined', 'pending'])
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### Module 8: Onboarding (Pre-boarding)

**Purpose:** Bridge the gap between offer acceptance and Day 1.

#### 4.8.1 Features

**Pre-boarding Portal (Candidate-facing)**
- Welcome page with company info, team intro, start date details
- Document collection:
  - Tax forms (W-4, I-9, etc.)
  - Direct deposit information
  - Emergency contacts
  - ID verification documents
  - NDA / confidentiality agreements
  - Benefits enrollment forms
- E-signature for employment documents
- Equipment preferences survey (laptop, monitor, peripherals)
- Profile photo upload
- Pre-reading materials and welcome content
- Team introduction videos or bios
- First-day logistics (where to go, what to bring, parking, dress code)

**Internal Onboarding Management**
- Onboarding checklist templates (per department/role)
- Task assignment to various teams (IT provisioning, facilities, security badge, etc.)
- Progress tracking dashboard
- Automated reminders for incomplete tasks
- Integration triggers (create accounts in HRIS, provision email, Slack invite, etc.)
- Buddy/mentor assignment

#### 4.8.2 API Endpoints

```
# Candidate-facing (token-based)
GET    /api/v1/onboarding/{token}/                     # Onboarding portal data
GET    /api/v1/onboarding/{token}/tasks/               # Task checklist
POST   /api/v1/onboarding/{token}/documents/           # Upload document
POST   /api/v1/onboarding/{token}/forms/{form_id}/     # Submit form

# Internal
GET    /api/v1/internal/onboarding/                    # List pending onboardings
GET    /api/v1/internal/onboarding/{id}/               # Detail + checklist
POST   /api/v1/internal/onboarding/{id}/tasks/         # Add task
PUT    /api/v1/internal/onboarding/{id}/tasks/{tid}/   # Update task status
POST   /api/v1/internal/onboarding/templates/          # Create checklist template
```

---

### Module 9: Communication Engine

**Purpose:** Centralized communication across the entire hiring lifecycle.

#### 4.9.1 Features

**Email**
- Template library with merge fields (candidate name, job title, interview date, etc.)
- Rich text email composer
- Bulk email (with personalization)
- Scheduled sending
- Email tracking (open, click, bounce)
- Auto-triggered emails (stage transitions, reminders, status updates)
- Reply tracking (candidate replies appear in application timeline)
- Unsubscribe handling

**In-App Messaging**
- Recruiter ↔ Candidate messaging
- Internal team messaging / comments on applications
- @mentions in notes and comments
- Thread-based conversations

**Notifications**
- In-app notification center (bell icon, unread count)
- Email notifications (digest or real-time, configurable)
- SMS notifications (interview reminders, offer alerts)
- Push notifications (mobile, if applicable)
- Webhook notifications (for integrations)
- Configurable notification preferences per user

**Templates**
- System-wide template library categorized by: stage, purpose, department
- Variable interpolation ({{candidate.first_name}}, {{job.title}}, etc.)
- A/B testing for email templates (optional)
- Template versioning
- Multi-language support

#### 4.9.2 Data Model

```python
class EmailTemplate(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(choices=TEMPLATE_CATEGORY_CHOICES)
    subject = models.CharField(max_length=500)
    body_html = models.TextField()
    body_text = models.TextField()
    variables = models.JSONField(default=list)  # Available merge fields
    department = models.ForeignKey('Department', null=True)  # null = global
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('InternalUser')
    version = models.IntegerField(default=1)

class EmailLog(models.Model):
    template = models.ForeignKey(EmailTemplate, null=True)
    application = models.ForeignKey('Application', null=True)
    sender = models.ForeignKey('InternalUser', null=True)
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=500)
    body = models.TextField()
    status = models.CharField(choices=['queued', 'sent', 'delivered', 'opened', 'clicked', 'bounced', 'failed'])
    sent_at = models.DateTimeField(null=True)
    opened_at = models.DateTimeField(null=True)
    message_id = models.CharField(blank=True)  # Email provider message ID

class Notification(models.Model):
    recipient = models.ForeignKey('User', related_name='notifications')
    notification_type = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    body = models.TextField()
    link = models.CharField(blank=True)
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### Module 10: Analytics & Reporting

**Purpose:** Data-driven hiring decisions with comprehensive metrics and reporting.

#### 4.10.1 Features

**Executive Dashboard**
- Hiring velocity (offers made vs. target, by department)
- Open requisition count and aging
- Time-to-fill by department, level, location
- Offer acceptance rate
- Pipeline health (conversion rates between stages)
- Headcount plan vs. actual
- Cost per hire
- Source effectiveness

**Recruiter Dashboard**
- Personal workload (open reqs, active candidates, pending tasks)
- Pipeline funnel per requisition
- Upcoming interviews and pending scorecards
- Overdue actions (reviews, feedback, approvals)
- SLA compliance (response time, time-in-stage)

**Reports**
- Pre-built report library:
  - Pipeline conversion report
  - Time-to-fill report
  - Source effectiveness report
  - Diversity report (EEO data, anonymized)
  - Offer analysis report (acceptance rate, decline reasons, negotiation patterns)
  - Interviewer activity and calibration report
  - Requisition aging report
  - Cost per hire report
  - Candidate experience survey results
- Custom report builder (select dimensions, metrics, filters, date ranges)
- Report scheduling (weekly/monthly email delivery)
- Export to CSV, Excel, PDF
- Data visualization (charts, graphs, trends)

**Compliance Reporting**
- EEO-1 report generation
- OFCCP compliance reporting
- Adverse impact analysis
- Audit log reports
- Data retention compliance reports

#### 4.10.2 API Endpoints

```
GET    /api/v1/internal/analytics/dashboard/executive/       # Executive dashboard data
GET    /api/v1/internal/analytics/dashboard/recruiter/       # Recruiter dashboard
GET    /api/v1/internal/analytics/pipeline/{req_id}/         # Pipeline funnel
GET    /api/v1/internal/analytics/time-to-fill/              # Time-to-fill metrics
GET    /api/v1/internal/analytics/source-effectiveness/      # Source ROI
GET    /api/v1/internal/analytics/diversity/                 # Diversity metrics
GET    /api/v1/internal/analytics/interviewer-calibration/   # Interviewer consistency
GET    /api/v1/internal/analytics/cost-per-hire/             # Cost analysis

POST   /api/v1/internal/reports/generate/                    # Generate custom report
GET    /api/v1/internal/reports/                             # List saved reports
GET    /api/v1/internal/reports/{id}/download/               # Download report
POST   /api/v1/internal/reports/{id}/schedule/               # Schedule recurring report

GET    /api/v1/internal/analytics/compliance/eeo/            # EEO reporting
GET    /api/v1/internal/analytics/compliance/adverse-impact/ # Adverse impact
```

---

### Module 11: Administration & Configuration

**Purpose:** System configuration, user management, and organizational settings.

#### 4.11.1 Features

**User Management**
- Internal user CRUD with role assignment
- Role-based access control (RBAC) with granular permissions
- Permission sets: view, create, edit, delete, approve — per module
- SSO integration (SAML 2.0, OIDC) for internal users
- Multi-factor authentication enforcement
- User provisioning via SCIM
- Session management and forced logout
- Login audit trail

**Organizational Structure**
- Company hierarchy (divisions → departments → teams)
- Office locations management
- Job levels / career ladder configuration
- Cost center mapping

**Workflow Configuration**
- Pipeline stage templates (create/edit default hiring stages)
- Approval workflow builder (requisition approvals, offer approvals)
- Automation rules engine:
  - Trigger: stage change, time elapsed, score threshold, etc.
  - Action: send email, assign task, move stage, notify, etc.
- Rejection reason library management
- Tag taxonomy management

**System Settings**
- Career site branding (logo, colors, fonts, custom CSS)
- Email sender configuration (domain, reply-to)
- Integration management (API keys, OAuth connections)
- Data retention policies
- Feature flags (enable/disable features per tenant)
- Audit log viewer

**Compliance Configuration**
- EEO question configuration
- Data retention rules
- GDPR consent management settings
- Right-to-be-forgotten workflow
- Data processing agreements

#### 4.11.2 RBAC Model

```python
class Role(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(default=False)  # Cannot be deleted
    permissions = models.ManyToManyField('Permission')

class Permission(models.Model):
    codename = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    module = models.CharField(max_length=50)  # e.g., 'requisitions', 'applications'
    action = models.CharField(max_length=20)  # 'view', 'create', 'edit', 'delete', 'approve'

class InternalUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey('Department')
    team = models.ForeignKey('Team', null=True)
    title = models.CharField(max_length=200)
    manager = models.ForeignKey('self', null=True)
    roles = models.ManyToManyField(Role)
    is_active = models.BooleanField(default=True)
    sso_id = models.CharField(blank=True)  # External SSO identifier
    last_login_ip = models.GenericIPAddressField(null=True)

# Default roles and their key permissions:
# Super Admin: Full system access
# HR Admin: User management, workflow config, compliance
# Recruiter: Requisitions, applications, pipeline, interviews, offers, comms
# Hiring Manager: Own department reqs, candidate review, interview feedback, approvals
# Interviewer: View assigned candidates, submit scorecards
# Coordinator: Schedule interviews, manage logistics
# Executive: Read-only dashboards and reports
# Onboarding Specialist: Onboarding management
```

---

### Module 12: Integrations

**Purpose:** Connect HR-Plus with the enterprise ecosystem.

#### 4.12.1 Integration Categories

**HRIS / HCM Systems**
- Workday, SAP SuccessFactors, BambooHR, ADP
- Sync: departments, employees (interviewers), job levels
- Push: new hire data upon offer acceptance

**Calendar & Scheduling**
- Google Calendar, Microsoft Outlook/365
- Bi-directional sync for interviewer availability
- Auto-create calendar events for interviews

**Video Conferencing**
- Zoom, Microsoft Teams, Google Meet
- Auto-generate meeting links for interviews

**Job Boards**
- Indeed, LinkedIn, Glassdoor, ZipRecruiter
- XML feed and API-based posting
- Application import (receive applications from external boards)

**Background Check Providers**
- Checkr, Sterling, HireRight
- Initiate checks from within the platform
- Receive results via webhook

**E-Signature**
- DocuSign, Adobe Sign, HelloSign
- Send offer letters for signature
- Track signature status

**Assessment Platforms**
- HackerRank, Codility, CoderPad (technical)
- Criteria Corp, Wonderlic (aptitude)
- Send invitations, receive results

**Communication**
- Slack (notifications, approvals via Slack)
- Microsoft Teams (same)
- SendGrid / SES (transactional email)
- Twilio (SMS)

**SSO / Identity**
- Okta, Azure AD, Google Workspace
- SAML 2.0 and OIDC support
- SCIM user provisioning

**Data & Analytics**
- Tableau, Looker, Power BI (data export / connector)
- Google Analytics (career site tracking)

#### 4.12.2 Integration Architecture

```python
class Integration(models.Model):
    provider = models.CharField(max_length=50)
    category = models.CharField(choices=INTEGRATION_CATEGORY_CHOICES)
    is_active = models.BooleanField(default=False)
    config = EncryptedJSONField()  # API keys, OAuth tokens, settings
    last_sync_at = models.DateTimeField(null=True)
    sync_status = models.CharField(choices=['ok', 'error', 'syncing'])
    error_log = models.TextField(blank=True)

class WebhookEndpoint(models.Model):
    url = models.URLField()
    secret = EncryptedCharField()
    events = ArrayField(models.CharField())  # Events to subscribe to
    is_active = models.BooleanField(default=True)
    failure_count = models.IntegerField(default=0)

class WebhookDelivery(models.Model):
    endpoint = models.ForeignKey(WebhookEndpoint)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    response_status = models.IntegerField(null=True)
    delivered_at = models.DateTimeField(null=True)
    attempts = models.IntegerField(default=0)
```

**Webhook Events Published:**
- `application.created`, `application.stage_changed`, `application.rejected`, `application.hired`
- `interview.scheduled`, `interview.completed`, `interview.cancelled`
- `offer.created`, `offer.sent`, `offer.accepted`, `offer.declined`
- `requisition.opened`, `requisition.filled`, `requisition.cancelled`
- `candidate.created`, `candidate.updated`

---

## 5. Compliance & Security

### 5.1 Data Privacy (GDPR, CCPA, and Global)

**Candidate Data Rights**
- Right to access: Candidates can export all their data (profile, applications, communications)
- Right to rectification: Candidates can update their information at any time
- Right to erasure: "Right to be forgotten" — anonymization workflow that removes PII while preserving aggregate metrics
- Right to data portability: Export in machine-readable format (JSON, CSV)
- Right to restrict processing: Candidates can pause their applications
- Consent management: Explicit consent collection at registration, per-purpose consent tracking
- Consent withdrawal: Easy opt-out with clear consequences explained

**Data Processing**
- Lawful basis tracking per data processing activity
- Data Processing Impact Assessments (DPIA) for AI/ML features
- Sub-processor management
- Cross-border data transfer controls (Standard Contractual Clauses support)
- Cookie consent management on career site

**Data Retention**
- Configurable retention policies per data type:
  - Active candidate data: retained while application is active
  - Unsuccessful applications: configurable (e.g., 12-24 months)
  - Hired employee data: transferred to HRIS, local copy retained per policy
  - Communication logs: retained per legal requirements
- Automated purge jobs (Celery Beat) with audit trail
- Legal hold capability (suspend deletion for litigation)

### 5.2 Equal Employment Opportunity (EEO) & Anti-Discrimination

- EEO-1 report generation (US)
- Voluntary self-identification collection (race, ethnicity, gender, veteran status, disability)
- Data stored separately from application data (firewall)
- Anonymized aggregate reporting only — never visible to hiring team
- OFCCP compliance: record-keeping, applicant flow logs, adverse impact analysis
- Bias detection in job descriptions (AI-powered language analysis)
- Structured interview enforcement to reduce subjective bias
- Adverse impact ratio calculation (four-fifths rule)

### 5.3 Security Architecture

**Authentication & Authorization**
- Candidate auth: email/password + social login, optional MFA
- Internal auth: SSO (SAML 2.0 / OIDC) with enforced MFA
- JWT tokens with short expiry (15 min access, 7 day refresh)
- Session management: concurrent session limits, forced logout
- Password policy enforcement (length, complexity, rotation)
- Account lockout after failed attempts
- IP-based access restrictions for internal portal (optional)

**Data Security**
- Encryption at rest (AES-256) for all PII fields
- Encryption in transit (TLS 1.3)
- Field-level encryption for sensitive data (SSN, salary, etc.)
- Database encryption (Transparent Data Encryption)
- File encryption for uploaded documents
- Key management via AWS KMS or HashiCorp Vault

**Application Security**
- OWASP Top 10 compliance
- CSRF protection (Django built-in)
- XSS prevention (Content Security Policy, input sanitization)
- SQL injection prevention (Django ORM, parameterized queries)
- Rate limiting (per endpoint, per user)
- API throttling
- Input validation (DRF serializers)
- File upload validation (type, size, malware scanning)
- Dependency vulnerability scanning (Dependabot, Snyk)

**Audit & Monitoring**
- Comprehensive audit log for all data access and modifications
- Who accessed what candidate data, when, from where
- All state changes logged with actor, timestamp, IP
- Audit log immutability (append-only, tamper-evident)
- Real-time security monitoring and alerting
- Failed login attempt monitoring
- Anomalous access pattern detection
- SOC 2 Type II compliance readiness

```python
class AuditLog(models.Model):
    actor = models.ForeignKey('User', null=True)  # null for system actions
    actor_ip = models.GenericIPAddressField(null=True)
    action = models.CharField(max_length=50)  # 'create', 'update', 'delete', 'view', 'export'
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=50)
    changes = models.JSONField(null=True)  # Before/after for updates
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['actor', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['timestamp']),
        ]
```

### 5.4 Infrastructure Security

- Network segmentation (VPC, private subnets for DB)
- WAF (Web Application Firewall)
- DDoS protection (CloudFlare or AWS Shield)
- Secrets management (no secrets in code, use Vault or AWS Secrets Manager)
- Container security scanning
- Regular penetration testing
- Incident response plan
- Disaster recovery with defined RPO/RTO
- Geo-redundant backups

---

## 6. Non-Functional Requirements

### 6.1 Performance

| Metric | Target |
|---|---|
| Job search response time | < 200ms (p95) |
| Page load (career site) | < 2s (LCP) |
| API response time | < 500ms (p95) |
| Pipeline board load | < 1s for 500 candidates |
| Concurrent users | 10,000+ candidates, 1,000+ internal |
| Search indexing delay | < 30 seconds |
| Email delivery | < 60 seconds from trigger |

### 6.2 Scalability

- Horizontal scaling for API servers (stateless Django behind load balancer)
- Database read replicas for reporting queries
- Elasticsearch cluster for search workload
- Celery worker auto-scaling based on queue depth
- CDN for static assets and career site
- Database connection pooling (PgBouncer)
- Caching strategy: Redis for sessions, frequently accessed data, and rate limiting

### 6.3 Availability

- Target: 99.9% uptime (8.7 hours downtime per year)
- Zero-downtime deployments (rolling updates)
- Health check endpoints
- Automated failover for database
- Queue persistence (Redis AOF/RDB for Celery)
- Graceful degradation (career site works if internal tools are down)

### 6.4 Accessibility

- WCAG 2.1 AA compliance (public career site — mandatory)
- WCAG 2.1 AA compliance (internal tools — target)
- Screen reader compatibility
- Keyboard navigation support
- Color contrast ratios
- Alt text for all images
- ARIA labels for interactive components
- Regular accessibility audits

### 6.5 Internationalization

- Multi-language career site (i18n framework)
- RTL language support
- Date, time, and number format localization
- Multi-currency support (offers, salary)
- Time zone handling throughout
- Unicode support for all text fields

### 6.6 Testing Strategy

| Level | Coverage Target | Tools |
|---|---|---|
| Unit tests (Django) | 80%+ | pytest, factory_boy |
| Unit tests (Next.js) | 80%+ | Jest, React Testing Library |
| Integration tests | Core workflows | pytest, DRF test client |
| E2E tests | Critical paths | Playwright |
| Performance tests | Key endpoints | Locust, k6 |
| Security tests | OWASP Top 10 | OWASP ZAP, Bandit |
| Accessibility tests | WCAG 2.1 AA | axe-core, pa11y |

---

## 7. Phased Delivery Plan

### Phase 1: Foundation (Weeks 1–8)
Core infrastructure, auth, basic job board, and candidate application flow.

- Project scaffolding (Next.js apps, Django project, Docker, CI/CD)
- Database schema and migrations
- Authentication (candidate + internal SSO)
- RBAC framework
- Job listing and search (basic)
- Career site with job detail pages
- Candidate registration and profile
- Basic application submission
- Admin: department and user management
- Audit logging foundation

### Phase 2: Hiring Pipeline (Weeks 9–16)
Requisition management, pipeline board, and interview scheduling.

- Requisition creation and approval workflow
- Pipeline / Kanban board
- Application review interface
- Candidate search and filtering
- Interview scheduling (manual + self-schedule)
- Calendar integration (Google, Outlook)
- Scorecard submission
- Email template engine and basic notifications
- Recruiter dashboard

### Phase 3: Advanced Hiring (Weeks 17–24)
Offers, assessments, advanced search, and communication.

- Offer management (create, approve, send, track)
- E-signature integration (DocuSign)
- Assessment module (take-home, coding challenge integration)
- Reference check automation
- Advanced candidate search (Elasticsearch)
- Bulk actions
- In-app messaging (recruiter ↔ candidate)
- Notification center
- Talent pools

### Phase 4: Intelligence & Compliance (Weeks 25–32)
Analytics, compliance, AI features, and onboarding.

- Analytics dashboards (executive + recruiter)
- Standard reports library
- Custom report builder
- EEO / OFCCP compliance reporting
- GDPR data subject rights (export, delete)
- AI resume scoring (optional feature flag)
- AI job description helper
- Pre-boarding portal
- Onboarding checklist management
- Background check integration

### Phase 5: Ecosystem & Polish (Weeks 33–40)
Integrations, optimization, and enterprise readiness.

- Job board distribution (Indeed, LinkedIn, Glassdoor)
- HRIS integration (Workday, etc.)
- Slack/Teams notifications
- Webhook system for external consumers
- Performance optimization
- Full accessibility audit and remediation
- Internationalization / localization
- Mobile-responsive polish
- Security audit and penetration testing
- Documentation (API docs, admin guide, user guide)
- Load testing and scalability validation

---

## 8. Key Technical Decisions

### 8.1 Two Separate Next.js Apps vs. One

**Recommendation: Two separate apps.**

- **Public app** (careers site): SSR/SSG-heavy for SEO, lighter auth, public caching, CDN-friendly, minimal client-side state.
- **Internal app** (staff dashboard): CSR-heavy with SSR for initial loads, complex state management, WebSocket connections, dense UI components.

Separate apps allow independent deployment, different caching strategies, and cleaner codebases. They share a common UI component library (internal npm package or monorepo shared package).

### 8.2 Django API Structure

**Recommendation: Modular Django apps within a single project.**

```
hr_plus/
├── config/                 # Settings, URLs, ASGI/WSGI
├── apps/
│   ├── accounts/           # User models, auth, SSO
│   ├── candidates/         # Candidate profiles, resumes
│   ├── jobs/               # Requisitions, job postings
│   ├── applications/       # Applications, pipeline
│   ├── interviews/         # Scheduling, scorecards
│   ├── assessments/        # Tests, reference checks
│   ├── offers/             # Offer management
│   ├── onboarding/         # Pre-boarding
│   ├── communications/     # Email, notifications, messaging
│   ├── analytics/          # Dashboards, reports
│   ├── integrations/       # External system connectors
│   ├── compliance/         # GDPR, EEO, audit
│   └── core/               # Shared utilities, base models, permissions
├── tasks/                  # Celery tasks
├── tests/
└── manage.py
```

### 8.3 API Versioning

Versioned API (`/api/v1/`) with deprecation policy. URL-based versioning for simplicity. New versions introduced only for breaking changes.

### 8.4 Multi-tenancy

**Recommendation: Single-tenant initially.** The platform is for a single large corporation. If multi-tenancy is needed later (e.g., selling as SaaS), the tenant-isolation layer can be added via django-tenants with schema-based isolation.

---

## 9. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Scope creep from stakeholder requests | High | High | Phased delivery, strict change control, product owner sign-off |
| Calendar integration complexity | Medium | High | Use established libraries (google-api-python-client, O365), abstract behind interface |
| GDPR compliance gaps | Medium | Critical | Engage legal counsel early, privacy-by-design, regular audits |
| AI bias in resume scoring | Medium | Critical | Bias testing, optional feature, human-in-the-loop, clear documentation |
| Performance at scale (large pipeline boards) | Medium | Medium | Pagination, virtualized lists, query optimization, caching |
| SSO integration complexity | Medium | Medium | Start with one provider (Okta or Azure AD), use proven libraries |
| Data migration from legacy ATS | High | Medium | Dedicated migration sprint, validation scripts, parallel running |
| Third-party integration reliability | Medium | Medium | Circuit breakers, retry logic, graceful degradation, monitoring |

---

## 10. Success Metrics

| Metric | Target | Measurement |
|---|---|---|
| Time to fill | Reduce by 25% within 6 months | Analytics module |
| Candidate application completion rate | > 80% | Funnel analytics |
| Offer acceptance rate | > 85% | Offer module reporting |
| Recruiter adoption | 100% of recruiters active within 30 days | User analytics |
| Career site SEO ranking | Top 3 for company name + "careers" | Google Search Console |
| System uptime | 99.9% | Infrastructure monitoring |
| Candidate satisfaction (post-application survey) | > 4.0/5.0 | Survey integration |
| Average candidate response time | < 48 hours | Communication analytics |

---

*Document version: 1.0*
*Last updated: February 14, 2026*
