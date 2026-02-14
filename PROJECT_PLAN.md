# HR-Plus — Comprehensive Project Plan

> **Version:** 1.0
> **Created:** 2026-02-14
> **Based on:** hr-platform-scope.md v1.0 + CLAUDE.md

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Summary](#2-architecture-summary)
3. [Development Environment Setup](#3-development-environment-setup)
4. [Phase 1: Foundation (Weeks 1–8)](#4-phase-1-foundation-weeks-18)
5. [Phase 2: Hiring Pipeline (Weeks 9–16)](#5-phase-2-hiring-pipeline-weeks-916)
6. [Phase 3: Advanced Hiring (Weeks 17–24)](#6-phase-3-advanced-hiring-weeks-1724)
7. [Phase 4: Intelligence & Compliance (Weeks 25–32)](#7-phase-4-intelligence--compliance-weeks-2532)
8. [Phase 5: Ecosystem & Polish (Weeks 33–40)](#8-phase-5-ecosystem--polish-weeks-3340)
9. [Cross-Cutting Concerns](#9-cross-cutting-concerns)
10. [Milestones & Deliverables](#10-milestones--deliverables)
11. [Risk Mitigation Plan](#11-risk-mitigation-plan)
12. [Definition of Done](#12-definition-of-done)

---

## 1. Project Overview

**HR-Plus** is a full-cycle enterprise hiring platform with two audiences:
- **External candidates** — public career site for job discovery, applications, and tracking
- **Internal staff** — recruiting dashboard for recruiters, hiring managers, interviewers, and HR admins

### Key Architectural Decisions
- **Split-stack**: Django API (source of truth) + two separate Next.js apps (public + internal)
- **Single-tenant initially** — designed for one large corporation
- **API versioned** at `/api/v1/` with URL-based versioning
- **Service layer pattern** — all business logic in Django services, never in views/serializers/frontend
- **RBAC enforced** at every endpoint

---

## 2. Architecture Summary

```
Monorepo Root
├── backend/                  # Django 5+ / DRF / Celery
│   ├── config/               # Settings, URLs, ASGI/WSGI
│   └── apps/                 # 12 Django apps (accounts, candidates, jobs, etc.)
├── apps/
│   ├── public-careers/       # Next.js 14+ — SSR/SSG career site
│   ├── internal-dashboard/   # Next.js 14+ — recruiter/HR dashboard
│   └── shared/               # Shared components, types, utilities
├── docker/                   # Dockerfiles per service
├── docker-compose.yml        # Development
└── docker-compose.prod.yml   # Production
```

### Infrastructure Components
| Service | Technology | Purpose |
|---------|-----------|---------|
| Database | PostgreSQL 16+ (pgvector) | Primary data store + semantic search |
| Cache/Broker | Redis 7 | Caching, sessions, Celery broker |
| Search | Elasticsearch 8 | Full-text job/candidate search |
| Task Queue | Celery + Beat | Async tasks, scheduled jobs |
| Realtime | Django Channels | WebSocket notifications |
| Storage | S3 / MinIO (dev) | File uploads (resumes, documents) |

---

## 3. Development Environment Setup

### Sprint 0 — Project Scaffolding (Week 0, pre-Phase 1)

This is prerequisite work before Phase 1 begins.

#### 3.1 Repository & Tooling
- [ ] Initialize git repository with `main`, `develop`, `staging` branches
- [ ] Configure branch protection rules (require PR reviews, passing CI)
- [ ] Set up commit convention enforcement (commitlint + Husky)
- [ ] Create `.gitignore` covering Python, Node, IDE files, `.env`
- [ ] Create `.env.example` with all required environment variables (no secrets)

#### 3.2 Docker Development Environment
- [ ] Create `docker-compose.yml` with services:
  - PostgreSQL 16 with pgvector extension
  - Redis 7
  - Elasticsearch 8
  - MinIO (S3-compatible storage for local dev)
  - Mailpit (local email testing)
- [ ] Create `docker/django/Dockerfile` (Python 3.12+, poetry/pip)
- [ ] Create `docker/nextjs-public/Dockerfile`
- [ ] Create `docker/nextjs-internal/Dockerfile`
- [ ] Verify all services start with `docker compose up -d`

#### 3.3 Django Project Setup
- [ ] Initialize Django 5+ project at `backend/`
- [ ] Configure split settings: `config/settings/{base,development,production}.py`
- [ ] Set up environment variable loading (no hardcoded secrets)
- [ ] Configure PostgreSQL connection with connection pooling
- [ ] Configure Redis for caching and sessions
- [ ] Install and configure Django REST Framework
- [ ] Install and configure `django-cors-headers`
- [ ] Install and configure `django-filter`
- [ ] Install and configure `drf-spectacular` (OpenAPI schema generation)
- [ ] Install and configure `django-cryptography` (field-level encryption)
- [ ] Set up Celery with Redis broker
- [ ] Set up Celery Beat for scheduled tasks
- [ ] Configure middleware stack in exact required order (per CLAUDE.md)
- [ ] Set up `pytest` with `pytest-django`, `factory-boy`, `pytest-cov`
- [ ] Configure `ruff` for linting and formatting
- [ ] Configure `mypy` for type checking
- [ ] Create `apps/core/` with:
  - `models.py` — Abstract base models (TimestampedModel, UUIDModel)
  - `permissions.py` — RBAC helpers
  - `services.py` — Base service class
  - `middleware.py` — AuditLogMiddleware, TenantMiddleware stubs
  - `utils.py` — Shared utilities
  - `exceptions.py` — Custom exception classes
  - `pagination.py` — StandardResultsSetPagination

#### 3.4 Next.js Public App Setup
- [ ] Initialize Next.js 14+ at `apps/public-careers/` (App Router only)
- [ ] Configure TypeScript strict mode
- [ ] Install and configure Tailwind CSS
- [ ] Install React Query (`@tanstack/react-query`)
- [ ] Set up `lib/dal.ts` — Data Access Layer with `server-only` import
- [ ] Set up `lib/auth.ts` — Session utilities
- [ ] Create `middleware.ts` with CSP headers
- [ ] Create `app/error.tsx` and `app/global-error.tsx`
- [ ] Configure Jest + React Testing Library
- [ ] Configure ESLint + Prettier
- [ ] Create basic layout with header, footer, navigation

#### 3.5 Next.js Internal App Setup
- [ ] Initialize Next.js 14+ at `apps/internal-dashboard/` (App Router only)
- [ ] Configure TypeScript strict mode
- [ ] Install and configure Tailwind CSS
- [ ] Install and configure shadcn/ui
- [ ] Install React Query (`@tanstack/react-query`)
- [ ] Install Zustand for global state management
- [ ] Set up `lib/dal.ts` — Data Access Layer with `server-only` import
- [ ] Set up `lib/auth/session.ts`, `lib/auth/permissions.ts`
- [ ] Create `middleware.ts` with CSP headers + auth redirect
- [ ] Create `app/error.tsx` and `app/global-error.tsx`
- [ ] Configure Jest + React Testing Library
- [ ] Configure Playwright for E2E tests
- [ ] Configure ESLint + Prettier
- [ ] Create dashboard layout shell (sidebar, header, main content area)

#### 3.6 Shared Package
- [ ] Initialize `apps/shared/` as internal package
- [ ] Set up root `package.json` with npm workspaces
- [ ] Create `apps/shared/types/` — placeholder for auto-generated API types
- [ ] Create `apps/shared/components/` — shared UI primitives (Button, Input, etc.)
- [ ] Create `apps/shared/utils/` — shared helper functions

#### 3.7 CI/CD Pipeline
- [ ] GitHub Actions workflow: `ci.yml`
  - Run `ruff check` + `ruff format --check` on Python
  - Run `mypy` on Python
  - Run `pytest` with coverage report
  - Run `npm run lint` on both Next.js apps
  - Run `npm run type-check` on both Next.js apps
  - Run `npm test` on both Next.js apps
  - Run `pip-audit` + `npm audit`
- [ ] GitHub Actions workflow: `deploy-staging.yml` (on merge to `staging`)
- [ ] GitHub Actions workflow: `deploy-production.yml` (on merge to `main`)

#### 3.8 Type Sync Pipeline
- [ ] Add `npm run sync-types` script to root `package.json`
  - Runs `python manage.py spectacular --file schema.yml`
  - Runs `npx openapi-typescript schema.yml -o apps/shared/types/api.ts`
- [ ] Document: run this after ANY Django model or serializer change

---

## 4. Phase 1: Foundation (Weeks 1–8)

**Goal:** Core infrastructure, authentication, basic job board, and candidate application flow. A candidate can browse jobs, register, and submit an application. Internal users can log in and manage departments/users.

### Sprint 1 (Weeks 1–2): User Models & Authentication

#### Django: `apps/accounts/`
- [ ] **Models:**
  - `User` — custom user model extending `AbstractUser` (email as username)
  - `InternalUser` — profile for staff (employee_id, department, team, title, manager, roles, sso_id)
  - `CandidateProfile` — profile for candidates (phone [encrypted], location, work_authorization, resume_file, resume_parsed, linkedin_url, portfolio_url, preferred_salary, profile_completeness, source)
  - `Role` — RBAC roles (name, description, is_system, permissions M2M)
  - `Permission` — granular permissions (codename, name, module, action)
- [ ] **Services:**
  - `AuthService` — registration, login, token management, password reset
  - `UserService` — CRUD for internal users, role assignment
- [ ] **Serializers:**
  - `RegisterSerializer`, `LoginSerializer`, `UserSerializer`, `InternalUserSerializer`, `CandidateProfileSerializer`
- [ ] **Views:**
  - `POST /api/v1/auth/register/` — candidate registration with email verification
  - `POST /api/v1/auth/login/` — login (returns HttpOnly session cookie)
  - `POST /api/v1/auth/logout/` — logout (clear session)
  - `GET /api/v1/auth/me/` — current user profile
  - `POST /api/v1/auth/password-reset/` — password reset flow
- [ ] **Permissions:**
  - `HasPermission` — base RBAC permission class
  - `IsCandidate`, `IsInternalUser` — role-based checks
- [ ] **Tests:**
  - Registration with valid/invalid data
  - Login with correct/incorrect credentials
  - Session cookie is HttpOnly and Secure
  - Permission checks enforce RBAC
  - Password reset flow
- [ ] **Seed data:**
  - Default roles: Super Admin, HR Admin, Recruiter, Hiring Manager, Interviewer, Coordinator, Executive, Onboarding Specialist
  - Default permissions per module (view, create, edit, delete, approve)

#### Django: `apps/compliance/`
- [ ] **Models:**
  - `AuditLog` — actor, actor_ip, action, resource_type, resource_id, changes, metadata, timestamp
- [ ] **Middleware:**
  - `AuditLogMiddleware` — log all API requests (excluding health checks)
- [ ] **Tests:**
  - Verify audit logs are created for API requests
  - Verify audit log fields are populated correctly

### Sprint 2 (Weeks 3–4): Organizational Structure & Internal Auth

#### Django: `apps/accounts/` (continued)
- [ ] **Models:**
  - `Department` — name, parent (self-referential for hierarchy), head (FK to InternalUser)
  - `Team` — name, department, lead
  - `Location` — name, city, country, address, is_remote
  - `JobLevel` — name, level_number, salary_band_min, salary_band_max
- [ ] **Services:**
  - `DepartmentService` — CRUD, hierarchy management
- [ ] **Views (internal):**
  - `GET/POST /api/v1/internal/departments/` — list/create departments
  - `GET/PUT /api/v1/internal/departments/{id}/` — detail/update
  - `GET/POST /api/v1/internal/users/` — list/create internal users
  - `GET/PUT /api/v1/internal/users/{id}/` — detail/update
  - `GET /api/v1/internal/locations/` — list office locations
  - `GET /api/v1/internal/job-levels/` — list job levels
- [ ] **SSO stub:**
  - SAML 2.0 / OIDC configuration interface (can be completed later; use username/password for internal users initially)
- [ ] **Tests:**
  - Department CRUD with proper permissions
  - Internal user creation with role assignment
  - Hierarchy queries (department tree)

#### Next.js Internal App: Login & Layout
- [ ] Login page (`app/(auth)/login/page.tsx`)
  - Email/password form
  - Server Action that proxies to Django auth endpoint
  - Sets HttpOnly session cookie
  - Redirects to dashboard
- [ ] Auth middleware — redirects unauthenticated users to `/login`
- [ ] Dashboard layout (`app/(dashboard)/layout.tsx`)
  - Sidebar navigation (Dashboard, Requisitions, Applications, Candidates, Interviews, Offers, Analytics, Settings)
  - Header with user avatar, notifications bell, logout
  - Permission-based nav item visibility
- [ ] Settings pages:
  - `app/(dashboard)/settings/departments/page.tsx` — department management
  - `app/(dashboard)/settings/users/page.tsx` — internal user management
  - `app/(dashboard)/settings/locations/page.tsx` — location management
- [ ] DAL functions: `getMe()`, `getDepartments()`, `getInternalUsers()`, `getLocations()`

### Sprint 3 (Weeks 5–6): Jobs & Career Site

#### Django: `apps/jobs/`
- [ ] **Models:**
  - `Requisition` — requisition_id, title, department, team, hiring_manager, recruiter, status, employment_type, level, location, remote_policy, salary_min/max, salary_currency, description, requirements_required/preferred, screening_questions, headcount, filled_count, target dates, version
  - `PipelineStage` — requisition FK, name, order, stage_type, auto_actions
- [ ] **Services:**
  - `RequisitionService` — create, update, publish, lifecycle management
  - `JobService` — public job listing logic, search, filtering
- [ ] **Selectors:**
  - `JobSelector` — `get_active_jobs()`, `get_job_by_slug()`, `get_similar_jobs()`, `get_categories()`
- [ ] **Serializers:**
  - `PublicJobListSerializer` (minimal fields for listing)
  - `PublicJobDetailSerializer` (full detail for job page)
  - `RequisitionSerializer` (internal, full fields)
- [ ] **Views (public):**
  - `GET /api/v1/jobs/` — paginated, filterable job listings
  - `GET /api/v1/jobs/{slug}/` — job detail page
  - `GET /api/v1/jobs/categories/` — department/category list
  - `GET /api/v1/jobs/{id}/similar/` — similar jobs
  - `GET /api/v1/locations/` — public office locations
- [ ] **Filters:**
  - `JobFilter` — keyword, department, location, employment_type, remote_policy, salary_range
- [ ] **Caching:**
  - Cache active jobs list for 5 minutes (Redis)
  - Cache job categories (long-lived)
- [ ] **Tests:**
  - Job listing pagination and filtering
  - Job detail with related data
  - Only published/open jobs appear publicly
  - Cache invalidation on job update

#### Next.js Public App: Career Site
- [ ] Homepage (`app/(public)/page.tsx`)
  - Hero section with search bar
  - Featured jobs
  - Department highlights
  - Company stats
- [ ] Job listings page (`app/(public)/jobs/page.tsx`)
  - Server-rendered job grid/list
  - Filters sidebar (department, location, type, remote)
  - Search input
  - Pagination
  - SEO: meta tags, canonical URLs
- [ ] Job detail page (`app/(public)/jobs/[slug]/page.tsx`)
  - Full job description with sections
  - Apply button (links to application flow)
  - Similar jobs sidebar
  - JSON-LD structured data for Google Jobs
  - Open Graph + Twitter Card meta tags
- [ ] DAL functions: `getJobs()`, `getJobBySlug()`, `getSimilarJobs()`, `getCategories()`
- [ ] Tests: job listing renders, filters work, SEO meta present

### Sprint 4 (Weeks 7–8): Candidate Application Flow

#### Django: `apps/candidates/` + `apps/applications/`
- [ ] **Models (candidates):**
  - `WorkExperience` — company, title, dates, is_current, description
  - `Education` — institution, degree, field, dates, gpa
  - `Skill` — name, proficiency, years_experience
- [ ] **Models (applications):**
  - `Application` — application_id, candidate, requisition, status, current_stage, source, referrer, resume_snapshot, cover_letter, screening_responses, tags, is_starred, rejection_reason, dates
  - `ApplicationEvent` — application, event_type, actor, from_stage, to_stage, metadata, timestamp
- [ ] **Services:**
  - `CandidateService` — profile CRUD, resume upload, profile completeness calculation
  - `ApplicationService` — create application (duplicate detection, auto-assign to first stage, confirmation email, event logging)
- [ ] **Views (candidate-facing):**
  - `GET/PUT /api/v1/candidates/profile/` — own profile
  - `POST /api/v1/candidates/resume/upload/` — upload and parse resume
  - `POST /api/v1/applications/` — submit application
  - `GET /api/v1/applications/` — list own applications
  - `GET /api/v1/applications/{id}/` — application detail + timeline
  - `POST /api/v1/applications/{id}/withdraw/` — withdraw
- [ ] **Resume parsing:**
  - Basic text extraction from PDF/DOCX (Celery task)
  - Store parsed data in `resume_parsed` JSONField
  - Full NLP parsing can be enhanced in Phase 4
- [ ] **Tests:**
  - Application creation with duplicate prevention
  - Application event logging
  - Candidate profile CRUD
  - Resume upload and parse
  - Application status filtering
  - Withdrawal flow

#### Next.js Public App: Candidate Portal
- [ ] Registration page (`app/(auth)/register/page.tsx`)
  - Name, email, password form
  - Server Action proxies to Django
  - Email verification flow
- [ ] Login page (`app/(auth)/login/page.tsx`)
  - Email/password + social login buttons (Google, LinkedIn stubs)
- [ ] Profile page (`app/dashboard/profile/page.tsx`)
  - Personal info form
  - Resume upload
  - Work experience management (add/edit/delete)
  - Education management
  - Skills management
  - Profile completeness indicator
- [ ] Application form (`app/(auth)/apply/[jobId]/page.tsx`)
  - Multi-step form:
    1. Review profile info
    2. Screening questions (from requisition config)
    3. Cover letter (optional)
    4. Review & submit
  - Server Action for submission
  - Success confirmation
- [ ] Applications dashboard (`app/dashboard/applications/page.tsx`)
  - List of all applications with status badges
  - Click to view timeline/detail
  - Withdraw button
- [ ] DAL functions: `getProfile()`, `updateProfile()`, `uploadResume()`, `createApplication()`, `getApplications()`, `getApplicationDetail()`
- [ ] Tests: registration flow, profile update, application submission, application list

### Phase 1 Milestone Checklist
- [ ] Candidate can browse jobs on career site with search and filters
- [ ] Candidate can register, build profile, upload resume
- [ ] Candidate can apply to a job and see application status
- [ ] Internal user can log in and manage departments, users, locations
- [ ] All API endpoints have auth + RBAC
- [ ] Audit logging captures all API activity
- [ ] 80%+ test coverage on backend
- [ ] CI pipeline passes (lint, type check, tests)
- [ ] Type sync pipeline works (Django → OpenAPI → TypeScript)

---

## 5. Phase 2: Hiring Pipeline (Weeks 9–16)

**Goal:** Recruiters can create requisitions with approval workflows, manage candidates through a pipeline board, schedule interviews, and submit scorecards.

### Sprint 5 (Weeks 9–10): Requisition Management

#### Django: `apps/jobs/` (continued)
- [ ] **Models:**
  - `RequisitionApproval` — requisition, approver, order, status, decided_at, comments, delegated_to
  - `InterviewPlan` — requisition, stage_name, stage_order, interview_type, duration, interviewer_count, scorecard_template, instructions
  - `RequisitionTemplate` — reusable requisition templates
- [ ] **Services:**
  - `RequisitionService` (extended) — submit for approval, approve, reject, publish, hold, cancel, clone
  - `ApprovalService` — process approval chain (sequential/parallel), send reminders, handle delegation
- [ ] **Views (internal):**
  - `POST /api/v1/internal/requisitions/` — create
  - `GET /api/v1/internal/requisitions/` — list (filterable by status, dept, recruiter)
  - `GET/PUT /api/v1/internal/requisitions/{id}/` — detail/update
  - `POST /api/v1/internal/requisitions/{id}/submit/` — submit for approval
  - `POST /api/v1/internal/requisitions/{id}/approve/` — approve
  - `POST /api/v1/internal/requisitions/{id}/reject/` — reject with reason
  - `POST /api/v1/internal/requisitions/{id}/publish/` — publish to career site
  - `POST /api/v1/internal/requisitions/{id}/hold/` — put on hold
  - `POST /api/v1/internal/requisitions/{id}/cancel/` — cancel
  - `POST /api/v1/internal/requisitions/{id}/clone/` — clone as new draft
  - `GET /api/v1/internal/approvals/pending/` — pending approvals for current user
- [ ] **Celery tasks:**
  - `send_approval_reminder` — notify approvers with pending items
  - `check_requisition_expiry` — auto-expire old requisitions
- [ ] **Tests:**
  - Full approval workflow (submit → approve → publish)
  - Rejection with revision cycle
  - Requisition state machine transitions
  - RBAC enforcement (only recruiters create, only approvers approve)
  - Clone creates correct copy

#### Next.js Internal App: Requisitions
- [ ] Requisitions list page (`app/(dashboard)/requisitions/page.tsx`)
  - Table with filters (status, department, recruiter, date)
  - Status badges
  - Quick actions (view, edit, clone)
- [ ] Requisition create/edit page (`app/(dashboard)/requisitions/new/page.tsx`)
  - Multi-step form:
    1. Job details (title, department, level, type, location, remote)
    2. Compensation (salary range, equity, bonus)
    3. Description (rich text editor)
    4. Requirements (required vs. preferred)
    5. Screening questions builder
    6. Hiring team assignment
    7. Interview plan (stages, types, scorecards)
    8. Review & save
- [ ] Requisition detail page (`app/(dashboard)/requisitions/[id]/page.tsx`)
  - Status with lifecycle actions (submit, approve, publish, etc.)
  - Approval chain visualization
  - Tab navigation: Details, Pipeline, Interviews, Analytics
- [ ] Pending approvals page (`app/(dashboard)/approvals/page.tsx`)
  - List of pending approvals with approve/reject actions

### Sprint 6 (Weeks 11–12): Pipeline Board & Application Management

#### Django: `apps/applications/` (continued)
- [ ] **Models:**
  - `Tag` — name, color, category
  - `RejectionReason` — reason text, category, is_active
  - `CandidateNote` — application, author, content, is_private, mentions
- [ ] **Services:**
  - `ApplicationService` (extended) — advance stage, move to specific stage, reject, transfer, bulk actions
  - `ApplicationEventService` — log all application events with metadata
- [ ] **Selectors:**
  - `ApplicationSelector` — `get_pipeline_board()` (optimized Kanban query), `search_applications()`, `get_application_detail_with_timeline()`
- [ ] **Views (internal):**
  - `GET /api/v1/internal/requisitions/{id}/pipeline/` — Kanban board data
  - `GET /api/v1/internal/applications/` — list/search with filters
  - `GET /api/v1/internal/applications/{id}/` — detail with full timeline
  - `POST /api/v1/internal/applications/{id}/advance/` — next stage
  - `POST /api/v1/internal/applications/{id}/move/` — specific stage
  - `POST /api/v1/internal/applications/{id}/reject/` — reject with reason
  - `POST /api/v1/internal/applications/{id}/notes/` — add note
  - `GET /api/v1/internal/applications/{id}/events/` — event timeline
  - `POST /api/v1/internal/applications/bulk/` — bulk move/reject/tag
- [ ] **Tests:**
  - Pipeline board query optimization (no N+1)
  - Stage transitions log events correctly
  - Rejection with reason and optional candidate email
  - Bulk actions process correctly
  - Notes with @mentions
  - RBAC: users only see applications in accessible departments

#### Next.js Internal App: Pipeline
- [ ] Pipeline board (`app/(dashboard)/requisitions/[id]/pipeline/page.tsx`)
  - Kanban columns (one per stage)
  - Candidate cards with summary info
  - Drag-and-drop between stages
  - Stage candidate counts
  - Quick filters (source, rating, tags)
  - Bulk selection with bulk actions bar
- [ ] Application detail modal/page
  - Candidate summary card
  - Resume viewer (PDF embed)
  - Screening responses
  - Notes section (add/view notes)
  - Activity timeline
  - Action buttons (advance, reject, schedule interview, send email)
  - Tags management
- [ ] Applications list page (`app/(dashboard)/applications/page.tsx`)
  - Global application table with advanced filters
  - Search by candidate name/email
  - Sort by date, status, stage

### Sprint 7 (Weeks 13–14): Interview Scheduling & Scorecards

#### Django: `apps/interviews/`
- [ ] **Models:**
  - `Interview` — application, interview_plan_stage, type, status, scheduled_start/end, timezone, location, video_link, prep notes, created_by
  - `InterviewParticipant` — interview, interviewer, role (lead/shadow/observer), rsvp_status
  - `Scorecard` — interview, interviewer, overall_rating, recommendation, strengths, concerns, notes, submitted_at, is_draft
  - `ScorecardCriterionRating` — scorecard, criterion, rating, comment
  - `ScorecardTemplate` — name, department, criteria, rating_scale
  - `ScorecardCriterion` — name, description, category
  - `Debrief` — application, scheduled_at, decision, notes, decided_by
- [ ] **Services:**
  - `InterviewService` — schedule, cancel, reschedule, assign participants
  - `ScorecardService` — create/submit/update scorecard, enforce independent feedback
  - `DebriefService` — create debrief, record decision
- [ ] **Selectors:**
  - `InterviewSelector` — `get_upcoming_interviews()`, `get_pending_scorecards()`, `get_interviewer_availability()`
- [ ] **Views (internal):**
  - `POST /api/v1/internal/interviews/` — schedule
  - `GET /api/v1/internal/interviews/` — list (filterable)
  - `GET/PUT /api/v1/internal/interviews/{id}/` — detail/update
  - `POST /api/v1/internal/interviews/{id}/cancel/`
  - `POST /api/v1/internal/interviews/{id}/scorecards/` — submit scorecard
  - `GET /api/v1/internal/interviews/{id}/scorecards/` — view (only after own submission)
  - `POST /api/v1/internal/applications/{id}/debrief/`
  - `PUT /api/v1/internal/debriefs/{id}/`
- [ ] **Views (candidate):**
  - `GET /api/v1/interviews/upcoming/` — candidate's interviews
  - `POST /api/v1/interviews/{id}/schedule/` — self-schedule from available slots
  - `POST /api/v1/interviews/{id}/reschedule/` — request reschedule
- [ ] **Anti-bias:**
  - Scorecards not visible to other interviewers until they submit their own
  - Structured criteria for consistent evaluation
- [ ] **Celery tasks:**
  - `send_interview_reminders` — 24h and 1h before
  - `send_scorecard_reminder` — after interview ends, nudge for feedback
- [ ] **Tests:**
  - Schedule/cancel/reschedule flow
  - Scorecard submission and independent feedback enforcement
  - Debrief decision recording
  - Candidate self-scheduling
  - Reminder task triggers

#### Next.js Internal App: Interviews
- [ ] Interview scheduling interface
  - Date/time picker
  - Interviewer selection with availability check
  - Interview type selection
  - Video link / room assignment
  - Prep notes for interviewer and candidate
- [ ] Scorecard submission form
  - Per-criterion ratings
  - Overall rating and recommendation
  - Strengths, concerns, notes
  - Draft save + final submit
- [ ] Debrief page
  - All scorecards side-by-side (after submission)
  - Consensus rating input
  - Decision buttons (Hire, No Hire, Hold)
- [ ] Interviews list (`app/(dashboard)/interviews/page.tsx`)
  - Upcoming interviews
  - Pending scorecards (overdue highlighted)

#### Next.js Public App: Candidate Interviews
- [ ] Upcoming interviews page (`app/dashboard/interviews/page.tsx`)
  - List of scheduled interviews
  - Details: who, when, where/link, what to prepare
  - Self-schedule interface (pick from available slots)
  - Add to calendar (iCal download)
  - Reschedule request

### Sprint 8 (Weeks 15–16): Email Templates & Recruiter Dashboard

#### Django: `apps/communications/`
- [ ] **Models:**
  - `EmailTemplate` — name, category, subject, body_html, body_text, variables, department, is_active, version
  - `EmailLog` — template, application, sender, recipient, subject, body, status (queued/sent/delivered/opened/bounced/failed), sent_at, opened_at, message_id
  - `Notification` — recipient, type, title, body, link, is_read, metadata, timestamp
- [ ] **Services:**
  - `EmailService` — render template with merge fields, send email via SMTP, queue for sending
  - `NotificationService` — create in-app notifications, mark as read
  - `TemplateService` — CRUD templates, variable interpolation
- [ ] **Celery tasks:**
  - `send_email_task` — async email delivery
  - `process_email_events` — handle delivery/open/bounce webhooks
- [ ] **Auto-triggered emails:**
  - Application confirmation (on submission)
  - Interview scheduled notification
  - Interview reminder (24h, 1h)
  - Application status update
- [ ] **Views (internal):**
  - `GET/POST /api/v1/internal/email-templates/` — template management
  - `POST /api/v1/internal/applications/{id}/send-email/` — send email to candidate
  - `GET /api/v1/internal/notifications/` — notification list
  - `POST /api/v1/internal/notifications/{id}/read/` — mark read
- [ ] **Tests:**
  - Template rendering with merge fields
  - Email queuing and delivery
  - Notification creation and read status
  - Auto-triggered emails fire correctly

#### Django: `apps/analytics/` (basic)
- [ ] **Selectors:**
  - `DashboardSelector` — `get_recruiter_dashboard()` (open reqs, active candidates, pending scorecards, upcoming interviews, overdue actions)
- [ ] **Views (internal):**
  - `GET /api/v1/internal/analytics/dashboard/recruiter/` — recruiter dashboard data
- [ ] **Tests:**
  - Dashboard data aggregation accuracy

#### Next.js Internal App: Communications & Dashboard
- [ ] Email template management page (`app/(dashboard)/settings/email-templates/page.tsx`)
  - List templates by category
  - Template editor with merge field insertion
  - Preview rendered template
- [ ] Send email modal (from application detail)
  - Template selection or freeform compose
  - Preview before send
- [ ] Notification center
  - Bell icon with unread count in header
  - Dropdown with recent notifications
  - Full notifications page
- [ ] Recruiter dashboard (`app/(dashboard)/dashboard/page.tsx`)
  - Key metrics cards (open reqs, active candidates, pending tasks)
  - Upcoming interviews list
  - Pending scorecards list
  - Recent activity feed
  - Overdue actions alerts

### Phase 2 Milestone Checklist
- [ ] Recruiter can create requisitions with approval workflows
- [ ] Approved requisitions publish to career site automatically
- [ ] Pipeline board shows candidates per stage with drag-and-drop
- [ ] Interviewers can schedule interviews and submit scorecards
- [ ] Candidates can self-schedule from available slots
- [ ] Auto-triggered emails for key events
- [ ] Recruiter dashboard with workload overview
- [ ] Notification system delivers in-app + email notifications
- [ ] All new endpoints have RBAC + audit logging
- [ ] 80%+ test coverage maintained

---

## 6. Phase 3: Advanced Hiring (Weeks 17–24)

**Goal:** Offer management with e-signature, assessments, advanced search with Elasticsearch, in-app messaging, and talent pools.

### Sprint 9 (Weeks 17–18): Offer Management

#### Django: `apps/offers/`
- [ ] **Models:**
  - `Offer` — offer_id, application, version, status, title, level, department, reporting_to, base_salary [encrypted], salary_currency/frequency, bonus, equity, sign_on_bonus, relocation, start_date, expiration_date, offer_letter_pdf, notes, sent_at, viewed_at, responded_at, decline_reason, esignature_envelope_id
  - `OfferNegotiationLog` — offer, logged_by, candidate_request, internal_response, outcome
  - `OfferApproval` — similar to RequisitionApproval
- [ ] **Services:**
  - `OfferService` — create, submit for approval, send to candidate, track response, revision management
  - `OfferApprovalService` — approval chain processing
  - `OfferLetterService` — PDF generation from template with merge fields
- [ ] **Views (internal):**
  - CRUD + lifecycle endpoints (draft → approve → send → track)
  - Negotiation log endpoints
- [ ] **Views (candidate):**
  - Token-based offer portal (view offer, accept/decline/discuss)
- [ ] **Tests:**
  - Offer lifecycle state machine
  - Salary encryption verified
  - Approval workflow
  - Candidate accept/decline flow
  - Offer versioning

#### Next.js Internal App: Offers
- [ ] Offer creation form (from application detail)
  - Compensation fields with currency support
  - Start date, expiration date
  - Offer letter template selection
  - Preview generated offer letter
- [ ] Offer detail page with lifecycle actions
- [ ] Negotiation log interface
- [ ] Offers list page with filters

#### Next.js Public App: Offer Portal
- [ ] Candidate offer view page (token-based)
  - Compensation breakdown visualization
  - Accept / Decline / Request Discussion buttons
  - Document upload (signed letter)

### Sprint 10 (Weeks 19–20): Assessments & Reference Checks

#### Django: `apps/assessments/`
- [ ] **Models:**
  - `Assessment` — type, application, status, assigned_at, due_date, completed_at, score
  - `AssessmentTemplate` — name, type, instructions, duration, scoring_rubric
  - `ReferenceCheckRequest` — application, reference contact info, questionnaire, status
  - `ReferenceCheckResponse` — request, responses (JSON), submitted_at
- [ ] **Services:**
  - `AssessmentService` — assign, track, score
  - `ReferenceCheckService` — send requests, collect responses, summarize
- [ ] **Views:**
  - Internal: assign/view assessments, request/view references
  - Candidate/Reference: token-based submission endpoints
- [ ] **Celery tasks:**
  - `send_reference_request` — email reference contacts
  - `send_assessment_reminder` — deadline approaching
- [ ] **Tests:**
  - Assessment assignment and completion flow
  - Reference request/response lifecycle
  - Token-based access security

#### Next.js Internal App: Assessments
- [ ] Assessment management (from application detail)
  - Assign assessment from template library
  - View results/scores
- [ ] Reference check interface
  - Request references (input reference contacts)
  - View response summaries

### Sprint 11 (Weeks 21–22): Advanced Search & Talent Pools

#### Django: Elasticsearch Integration
- [ ] **Search indexing:**
  - Job index (title, description, requirements, department, location)
  - Candidate index (name, email, skills, experience, resume_parsed)
- [ ] **Services:**
  - `CandidateSearchService` — Elasticsearch-powered search with:
    - Full-text search across resumes and profiles
    - Filters: skills, experience years, location, education, source, tags
    - Typo tolerance and synonym matching
    - Fallback to database ILIKE if ES unavailable
  - `JobSearchService` — enhanced job search with ES
- [ ] **Celery tasks:**
  - `index_candidate` — index/update candidate on profile change
  - `index_job` — index/update job on publish/update
  - `reindex_all` — full reindex task
- [ ] **Tests:**
  - Search returns relevant results
  - Filters narrow correctly
  - Fallback to database works

#### Django: `apps/applications/` — Talent Pools
- [ ] **Models:**
  - `TalentPool` — name, description, owner, candidates (M2M), is_dynamic, search_criteria
- [ ] **Services:**
  - `TalentPoolService` — create, add/remove candidates, dynamic pool auto-update
- [ ] **Views:**
  - CRUD for talent pools, add/remove candidates
- [ ] **Tests:**
  - Pool creation and candidate management
  - Dynamic pool updates based on search criteria

#### Next.js Internal App: Search & Talent Pools
- [ ] Global candidate search page (`app/(dashboard)/candidates/page.tsx`)
  - Search bar with advanced filters
  - Results with candidate summary cards
  - Actions: add to pool, view profile, add to requisition
- [ ] Candidate profile page (`app/(dashboard)/candidates/[id]/page.tsx`)
  - Full profile view
  - Application history across all requisitions
  - Notes and activity
- [ ] Talent pools page (`app/(dashboard)/talent-pools/page.tsx`)
  - List pools
  - Pool detail: candidate list with actions
  - Create pool from search results

### Sprint 12 (Weeks 23–24): In-App Messaging & Bulk Actions

#### Django: `apps/communications/` (continued)
- [ ] **Models:**
  - `MessageThread` — participants, application (optional), subject, created_at
  - `Message` — thread, sender, body, read_by (JSONField), attachments, created_at
- [ ] **Services:**
  - `MessagingService` — create thread, send message, mark read
- [ ] **Views (candidate + internal):**
  - `GET /api/v1/messages/` — list threads
  - `GET /api/v1/messages/{thread_id}/` — thread messages
  - `POST /api/v1/messages/{thread_id}/reply/` — send message
  - `PUT /api/v1/notifications/preferences/` — notification preferences
- [ ] **WebSocket (optional, can defer):**
  - Real-time message delivery via Django Channels
- [ ] **Tests:**
  - Thread creation and message exchange
  - Read receipts
  - Candidate can only see own threads

#### Next.js Internal App: Messaging
- [ ] Messages interface (sidebar or dedicated page)
  - Thread list with unread indicators
  - Message thread view
  - Compose message (from application or standalone)

#### Next.js Public App: Messaging
- [ ] Candidate messages page (`app/dashboard/messages/page.tsx`)
  - Thread list
  - Reply interface

#### Bulk Actions Enhancement
- [ ] Internal app: bulk selection toolbar on pipeline and application list
  - Bulk move to stage
  - Bulk reject with reason
  - Bulk tag/untag
  - Bulk send email

### Phase 3 Milestone Checklist
- [ ] Full offer lifecycle: create → approve → send → accept/decline
- [ ] Assessments can be assigned and completed
- [ ] Reference checks can be requested and collected
- [ ] Elasticsearch powers candidate and job search
- [ ] Talent pools for proactive recruiting
- [ ] In-app messaging between recruiters and candidates
- [ ] Bulk actions for efficient pipeline management
- [ ] All new endpoints maintain security + audit standards

---

## 7. Phase 4: Intelligence & Compliance (Weeks 25–32)

**Goal:** Analytics dashboards, compliance reporting (EEO/GDPR), AI features (resume scoring, JD helper), and onboarding portal.

### Sprint 13 (Weeks 25–26): Analytics Dashboards

#### Django: `apps/analytics/`
- [ ] **Selectors:**
  - `ExecutiveDashboardSelector` — hiring velocity, open req count/aging, time-to-fill, offer acceptance rate, pipeline conversion, headcount plan vs actual, cost per hire, source effectiveness
  - `ReportSelector` — pipeline conversion, time-to-fill, source effectiveness, offer analysis, interviewer calibration, requisition aging
- [ ] **Services:**
  - `ReportService` — generate custom reports, export CSV/Excel/PDF
  - `ReportScheduleService` — schedule recurring reports via Celery Beat
- [ ] **Views:**
  - `GET /api/v1/internal/analytics/dashboard/executive/`
  - `GET /api/v1/internal/analytics/pipeline/{req_id}/`
  - `GET /api/v1/internal/analytics/time-to-fill/`
  - `GET /api/v1/internal/analytics/source-effectiveness/`
  - `GET /api/v1/internal/analytics/interviewer-calibration/`
  - `GET /api/v1/internal/analytics/cost-per-hire/`
  - `POST /api/v1/internal/reports/generate/`
  - `GET /api/v1/internal/reports/{id}/download/`
- [ ] **Tests:**
  - Dashboard data accuracy
  - Report generation with correct aggregations
  - Export formats generate correctly

#### Next.js Internal App: Analytics
- [ ] Executive dashboard (`app/(dashboard)/analytics/page.tsx`)
  - KPI cards (time-to-fill, offer rate, open reqs, etc.)
  - Pipeline funnel chart
  - Hiring velocity trends
  - Source effectiveness chart
  - Department breakdown
- [ ] Reports page (`app/(dashboard)/analytics/reports/page.tsx`)
  - Pre-built report library
  - Custom report builder (select metrics, filters, date range)
  - Export buttons (CSV, Excel, PDF)
  - Schedule recurring delivery

### Sprint 14 (Weeks 27–28): Compliance — EEO & GDPR

#### Django: `apps/compliance/` (continued)
- [ ] **Models:**
  - `EEOData` — candidate FK, gender [encrypted], race_ethnicity [encrypted], veteran_status [encrypted], disability_status [encrypted], consent, collected_at
  - `ConsentRecord` — user, consent_type, given_at, withdrawn_at, ip_address
  - `AnonymizationRecord` — candidate_id, anonymized_at, reason
  - `DataRetentionPolicy` — data_type, retention_days, is_active
- [ ] **Services:**
  - `GDPRService` — export_candidate_data, anonymize_candidate, process_data_retention
  - `EEOService` — generate_eeo_report (aggregates only), adverse_impact_analysis
- [ ] **Views:**
  - `GET /api/v1/internal/analytics/compliance/eeo/` — EEO-1 report
  - `GET /api/v1/internal/analytics/compliance/adverse-impact/`
  - `GET /api/v1/internal/compliance/audit-log/` — searchable audit log viewer
- [ ] **Views (candidate):**
  - `GET /api/v1/candidates/data-export/` — export all own data (JSON)
  - `POST /api/v1/candidates/data-deletion/` — request data deletion
- [ ] **Celery tasks:**
  - `process_data_retention` — scheduled purge of expired data with audit trail
  - `generate_scheduled_eeo_report` — periodic EEO reporting
- [ ] **Tests:**
  - EEO data never visible to hiring team
  - Data export includes all candidate data
  - Anonymization removes PII but preserves aggregate stats
  - Retention policies execute correctly

#### Next.js Internal App: Compliance
- [ ] EEO reporting page (`app/(dashboard)/analytics/compliance/page.tsx`)
  - Anonymized aggregate charts
  - EEO-1 report export
  - Adverse impact calculator
- [ ] Audit log viewer (`app/(dashboard)/settings/audit-log/page.tsx`)
  - Searchable/filterable audit trail
  - Date range, actor, resource type filters
- [ ] Data retention settings

#### Next.js Public App: Candidate Data Rights
- [ ] EEO self-identification form (during application, always optional)
- [ ] Data export page (`app/dashboard/settings/data/page.tsx`)
  - Export all data button
  - Request deletion button
  - Consent management

### Sprint 15 (Weeks 29–30): AI Features

#### Django: AI Services
- [ ] **Services:**
  - `ResumeScoreService` — score resume against job requirements
    - Compare skills, experience, education to requisition requirements
    - Generate breakdown scores per category
    - Feature flag to enable/disable
  - `JobDescriptionAIService` — suggest improvements, check for biased language
    - Bias detection (gendered language, exclusionary terms)
    - Readability improvements
    - Missing section suggestions
- [ ] **Integration:**
  - pgvector for semantic similarity search (resume embeddings)
  - Celery task for async AI scoring on application submission
- [ ] **Tests:**
  - AI scoring produces consistent results
  - Bias detection catches known problematic terms
  - Feature flag properly disables AI scoring
  - Results stored correctly in application

#### Next.js Internal App: AI Features
- [ ] AI score display on application card and detail (when enabled)
  - Score badge with breakdown tooltip
  - "AI-assisted" label clearly visible
- [ ] JD helper in requisition creation
  - "Check for bias" button
  - "Improve description" suggestions
  - Clear AI attribution

### Sprint 16 (Weeks 31–32): Onboarding Portal

#### Django: `apps/onboarding/`
- [ ] **Models:**
  - `OnboardingPlan` — application/offer, status, start_date, buddy/mentor
  - `OnboardingTask` — plan, title, description, assigned_to, due_date, status, category
  - `OnboardingDocument` — plan, document_type, file, status, uploaded_at
  - `OnboardingForm` — plan, form_type, data (JSON), submitted_at
  - `OnboardingTemplate` — name, department, tasks (JSON)
- [ ] **Services:**
  - `OnboardingService` — create plan from template on offer acceptance, manage tasks, track progress
- [ ] **Views (candidate — token-based):**
  - `GET /api/v1/onboarding/{token}/` — portal data
  - `GET /api/v1/onboarding/{token}/tasks/` — checklist
  - `POST /api/v1/onboarding/{token}/documents/` — upload document
  - `POST /api/v1/onboarding/{token}/forms/{form_id}/` — submit form
- [ ] **Views (internal):**
  - Onboarding management dashboard
  - Task management
  - Template management
- [ ] **Tests:**
  - Onboarding plan auto-created on offer acceptance
  - Task completion tracking
  - Document upload and form submission

#### Next.js Public App: Onboarding Portal
- [ ] Token-based onboarding page
  - Welcome content
  - Task checklist with completion tracking
  - Document upload forms
  - Equipment preferences survey
  - First-day logistics info

#### Next.js Internal App: Onboarding Management
- [ ] Onboarding dashboard (`app/(dashboard)/onboarding/page.tsx`)
  - Pending onboardings with progress indicators
  - Task assignment and tracking
  - Template management

### Phase 4 Milestone Checklist
- [ ] Executive and recruiter dashboards with key metrics
- [ ] Custom report builder with export capabilities
- [ ] EEO-1 report generation with anonymized data
- [ ] GDPR: data export, deletion, consent management
- [ ] AI resume scoring (behind feature flag)
- [ ] AI bias detection for job descriptions
- [ ] Pre-boarding portal for new hires
- [ ] Onboarding task management for HR

---

## 8. Phase 5: Ecosystem & Polish (Weeks 33–40)

**Goal:** External integrations, performance optimization, accessibility audit, internationalization, security hardening, and production readiness.

### Sprint 17 (Weeks 33–34): Job Board & HRIS Integrations

#### Django: `apps/integrations/`
- [ ] **Models:**
  - `Integration` — provider, category, is_active, config [encrypted], last_sync, sync_status, error_log
  - `WebhookEndpoint` — url, secret [encrypted], events, is_active, failure_count
  - `WebhookDelivery` — endpoint, event_type, payload, response_status, delivered_at, attempts
- [ ] **Services:**
  - `IntegrationService` — manage integration lifecycle, handle OAuth flows
  - `JobBoardService` — push jobs to Indeed/LinkedIn/Glassdoor, import applications
  - `HRISService` — sync departments/employees, push new hire data
  - `WebhookService` — dispatch webhook events with retry logic
- [ ] **Webhook events:**
  - `application.created`, `application.stage_changed`, `application.rejected`, `application.hired`
  - `offer.created`, `offer.sent`, `offer.accepted`, `offer.declined`
  - `requisition.opened`, `requisition.filled`, `requisition.cancelled`
- [ ] **Tests:**
  - Integration CRUD with encrypted config
  - Webhook delivery with retry
  - Job board posting format
  - Circuit breaker on integration failure

### Sprint 18 (Weeks 35–36): Communication Integrations & E-Signature

#### Django: Integration Services (continued)
- [ ] **Calendar integration:**
  - Google Calendar API — bi-directional availability sync
  - Microsoft Graph API — Outlook calendar sync
  - Auto-create calendar events for interviews
- [ ] **Video conferencing:**
  - Zoom API — auto-generate meeting links
  - Google Meet / Teams link generation
- [ ] **E-Signature:**
  - DocuSign API integration — send offer letter, track status, receive completed docs
- [ ] **Communication:**
  - Slack API — notification delivery, approval actions
  - SendGrid / SES — transactional email provider
- [ ] **Tests:**
  - Calendar sync creates correct events
  - Video links generate and attach to interviews
  - DocuSign envelope lifecycle
  - Slack notification delivery

#### Next.js Internal App: Integration Management
- [ ] Integrations settings page (`app/(dashboard)/settings/integrations/page.tsx`)
  - Available integrations with connect/disconnect
  - OAuth connection flows
  - Integration status indicators
  - Webhook endpoint management

### Sprint 19 (Weeks 37–38): Performance, Accessibility & i18n

#### Performance Optimization
- [ ] **Django:**
  - Query audit — identify and fix N+1 queries across all views
  - Add database indexes on all frequently queried fields
  - Implement query-level caching for hot paths (dashboard, pipeline)
  - Connection pooling with PgBouncer
  - Optimize Celery task serialization
  - API response compression
- [ ] **Next.js (both apps):**
  - Implement virtual scrolling for pipeline board (large candidate lists)
  - Dynamic imports for heavy components (code splitting)
  - Image optimization with `next/image`
  - Review and optimize caching strategy (revalidate values)
  - Bundle size analysis and reduction
  - Lazy load below-fold content
- [ ] **Load testing:**
  - Set up Locust or k6 test suite
  - Test: 10,000 concurrent candidates, 1,000 internal users
  - Pipeline board load < 1s for 500 candidates
  - Job search response < 200ms (p95)
  - API response < 500ms (p95)

#### Accessibility Audit (WCAG 2.1 AA)
- [ ] **Public career site (mandatory):**
  - Run axe-core audit on all pages
  - Keyboard navigation on all interactive elements
  - Screen reader testing (NVDA/JAWS/VoiceOver)
  - Color contrast verification
  - Alt text for all images
  - ARIA labels for custom components
  - Focus management on modals and dynamic content
  - Form error announcements
- [ ] **Internal dashboard (target):**
  - Same audit as public (priority: pipeline board, forms, navigation)
  - Drag-and-drop accessible alternative (keyboard stage move)

#### Internationalization
- [ ] **Django:**
  - Enable `django.middleware.locale.LocaleMiddleware`
  - Mark strings for translation (`gettext`)
  - Multi-currency support in offers
  - Time zone handling in all date/time fields
- [ ] **Next.js Public App:**
  - Set up `next-intl` or similar i18n framework
  - Extract all user-facing strings
  - RTL layout support
  - Date/number format localization
- [ ] **Next.js Internal App:**
  - Same i18n setup (lower priority for initial launch)

### Sprint 20 (Weeks 39–40): Security Hardening & Production Readiness

#### Security Hardening
- [ ] **Django production settings verified:**
  - HSTS enabled (31536000s)
  - SSL redirect
  - Secure cookies (HttpOnly, Secure, SameSite=Lax)
  - CSRF protection
  - X-Frame-Options: DENY
  - Content-Type nosniff
  - CORS limited to frontend origins only
- [ ] **Next.js production settings:**
  - CSP headers with nonces
  - X-Frame-Options: DENY
  - Referrer-Policy: strict-origin-when-cross-origin
- [ ] **Dependency audit:**
  - `pip-audit` — no critical/high vulnerabilities
  - `npm audit` — no critical/high vulnerabilities
  - `bandit` — Python security scan clean
- [ ] **Rate limiting:**
  - Authentication endpoints: 5 req/min
  - API endpoints: per-user throttling
  - Public endpoints: per-IP throttling
- [ ] **File upload security:**
  - Type validation (whitelist allowed MIME types)
  - Size limits
  - Malware scanning integration (ClamAV or similar)
- [ ] **Penetration testing:**
  - OWASP ZAP automated scan
  - Manual review of auth flows, RBAC, data access
  - Report and remediate findings

#### Production Deployment
- [ ] **Infrastructure:**
  - `docker-compose.prod.yml` finalized
  - Health check endpoints: `/api/health/` (Django), readiness/liveness probes
  - Zero-downtime deployment strategy (rolling updates)
  - Database backup automation
  - Log aggregation (ELK or similar)
  - Error tracking (Sentry)
  - Performance monitoring (Prometheus + Grafana or APM)
- [ ] **Documentation:**
  - API documentation (auto-generated from drf-spectacular)
  - Admin guide (system configuration, user management)
  - Deployment runbook
  - Incident response playbook

### Phase 5 Milestone Checklist
- [ ] Job board distribution working (Indeed, LinkedIn, Glassdoor)
- [ ] Calendar integration syncing availability
- [ ] E-signature integration for offers
- [ ] Slack notifications working
- [ ] Performance targets met under load
- [ ] WCAG 2.1 AA compliance verified (public site)
- [ ] i18n framework in place with at least one additional locale
- [ ] Security audit passed with no critical findings
- [ ] Production deployment pipeline operational
- [ ] Monitoring and alerting in place

---

## 9. Cross-Cutting Concerns

These apply throughout all phases and must be maintained continuously.

### Security
- Every API endpoint has explicit `permission_classes`
- All PII fields use field-level encryption
- Session cookies are HttpOnly, Secure, SameSite=Lax
- No raw SQL — ORM only
- No secrets in code — environment variables only
- Input validation on every endpoint (DRF serializers + Zod in Next.js)
- RBAC enforced: users only see data in accessible departments
- Audit logging on all data access and modifications

### Testing
- 80%+ code coverage maintained (Django + Next.js)
- Every new feature includes unit + integration tests
- E2E tests for critical paths (apply, interview, offer)
- Tests run in CI on every PR
- No merge without green CI

### Code Quality
- Max 300 lines per file, max 50 lines per function
- Service layer pattern: business logic in services, not views/serializers
- Selector pattern: complex queries in selectors
- DAL pattern: all Django API calls through data access layer
- Type safety: auto-generated TypeScript types from OpenAPI schema
- Linting clean: `ruff` (Python), `eslint` (TypeScript)

### Performance
- All list queries use `select_related` / `prefetch_related`
- All list endpoints paginated (max 100 per page)
- Redis caching for hot paths
- Appropriate `next: { revalidate }` values for all fetches
- No N+1 queries

### Type Sync Workflow
After any Django model or serializer change:
1. `python manage.py spectacular --file schema.yml`
2. `npx openapi-typescript schema.yml -o apps/shared/types/api.ts`
3. Commit the updated `api.ts`

---

## 10. Milestones & Deliverables

| Week | Milestone | Key Deliverable |
|------|-----------|----------------|
| 0 | Sprint 0 Complete | Dev environment, CI/CD, project scaffolding |
| 2 | Auth Complete | User registration, login, RBAC framework, audit logging |
| 4 | Org Structure | Departments, teams, locations, internal user management |
| 6 | Career Site Live | Job listings, search, detail pages (SEO-optimized) |
| 8 | **Phase 1 Complete** | **Candidates can browse, register, and apply** |
| 10 | Requisitions | Req creation, approval workflows, publish to career site |
| 12 | Pipeline Board | Kanban view, stage transitions, application management |
| 14 | Interviews | Scheduling, scorecards, debriefs, candidate self-schedule |
| 16 | **Phase 2 Complete** | **Full recruiter workflow: req → pipeline → interview** |
| 18 | Offers | Offer lifecycle, approval, candidate portal |
| 20 | Assessments | Assessments, reference checks |
| 22 | Advanced Search | Elasticsearch integration, talent pools |
| 24 | **Phase 3 Complete** | **End-to-end hiring: apply → interview → offer** |
| 26 | Analytics | Executive + recruiter dashboards, reports |
| 28 | Compliance | EEO reporting, GDPR data rights |
| 30 | AI Features | Resume scoring, JD bias detection |
| 32 | **Phase 4 Complete** | **Intelligence and compliance layer** |
| 34 | Integrations 1 | Job boards, HRIS sync |
| 36 | Integrations 2 | Calendar, video, e-signature, Slack |
| 38 | Performance + a11y | Load testing, accessibility audit, i18n |
| 40 | **Phase 5 Complete** | **Production-ready, fully integrated platform** |

---

## 11. Risk Mitigation Plan

| Risk | Mitigation |
|------|-----------|
| **Scope creep** | Phased delivery with clear milestones. Each phase has a defined "done" checklist. Changes go through product owner approval. |
| **Calendar integration complexity** | Abstract behind interface. Start with Google Calendar, add Outlook later. Use proven libraries. |
| **GDPR compliance gaps** | Privacy-by-design from Phase 1. Legal review at Phase 4. EEO data always segregated. |
| **AI bias in resume scoring** | Feature flagged, human-in-the-loop, bias testing, clear labeling as AI-assisted. |
| **Performance at scale** | Pagination everywhere, virtual scrolling, query optimization, caching. Load test at Phase 5. |
| **SSO integration complexity** | Start with password auth for internal users. Add SSO in Phase 2-3 with one provider first. |
| **Third-party integration reliability** | Circuit breakers, retry with exponential backoff, graceful degradation, integration health monitoring. |
| **Data migration (if from legacy ATS)** | Dedicated migration sprint (can be inserted between phases). Validation scripts, parallel running. |

---

## 12. Definition of Done

A feature is "done" when:

1. **Code complete** — implementation matches requirements
2. **Tests pass** — unit, integration, and E2E tests written and passing
3. **Coverage maintained** — 80%+ on modified modules
4. **Linting clean** — `ruff check`, `npm run lint`, `mypy`, `npm run type-check` all pass
5. **Security verified** — RBAC enforced, input validated, no PII leaks, audit logged
6. **Types synced** — if Django models/serializers changed, TypeScript types regenerated
7. **Code reviewed** — at least one peer review on PR
8. **No debugging artifacts** — no `console.log`, `print()`, `debugger`, or TODO hacks
9. **Documentation updated** — API docs auto-generated, significant decisions documented
10. **Accessible** — keyboard navigable, screen reader compatible (public site mandatory)

---

*This plan is a living document. Update it as requirements evolve, risks materialize, or technical decisions change.*
