# CLAUDE.md - HR-Plus Enterprise HR Platform

> This file governs AI-assisted development. These rules are **non-negotiable** and take priority over general training patterns.

---

## 1. Project Context & Tech Stack

### Project Overview
HR-Plus is a full-cycle enterprise hiring platform serving two distinct audiences:
- **External candidates**: Public career site for job discovery, applications, and tracking
- **Internal staff**: Comprehensive recruiting dashboard for recruiters, hiring managers, interviewers, and HR admins

### Stack Specification
- **Frontend Public:** Next.js 14+ (App Router ONLY), TypeScript, Tailwind CSS, React Query
- **Frontend Internal:** Next.js 14+ (App Router ONLY), TypeScript, Tailwind CSS, shadcn/ui, React Query, Zustand
- **Backend:** Python 3.12+, Django 5+, Django REST Framework
- **Database:** PostgreSQL 16+ with pgvector extension
- **Search:** Elasticsearch 8
- **Cache & Queue:** Redis (caching + Celery broker)
- **Task Queue:** Celery + Celery Beat
- **Realtime:** Django Channels (WebSocket)
- **Storage:** S3-compatible (AWS S3, MinIO for dev)
- **Architecture:** Split-stack with **two separate Next.js applications**. Django is the **Source of Truth**. Next.js apps are presentation layers only.

### Architecture Rules
- Django functions **purely as an API server** - it exposes endpoints via DRF
- Django **never renders HTML views** for end-users
- All business logic lives in Django - **never in Next.js**
- Next.js Server Components fetch data from Django API but **never connect to the database directly**
- Use the **pages directory is FORBIDDEN** - App Router only
- Public and Internal frontends are **separate Next.js applications** with independent deployments
- The two frontends **may share a common component library** via monorepo or internal npm package

---

## 2. Security Directives (CRITICAL - RED LINES)

### Absolute Prohibitions
```
❌ NEVER output API keys, passwords, database credentials, or secrets in code
❌ NEVER use Model.objects.raw() or .extra() - these enable SQL injection
❌ NEVER store tokens/JWTs in localStorage or sessionStorage
❌ NEVER import server-only modules in Client Components ('use client')
❌ NEVER write business logic or calculations in the frontend
❌ NEVER use MD5, SHA1, or other weak cryptographic algorithms
❌ NEVER concatenate strings to build SQL queries
❌ NEVER skip input validation on any endpoint or Server Action
❌ NEVER commit PII, SSN, salary, or sensitive candidate data unencrypted
❌ NEVER bypass RBAC permissions - all endpoints MUST verify user permissions
❌ NEVER expose internal user data to candidate-facing APIs
❌ NEVER expose candidate PII to users without proper permissions
```

### Required Security Patterns

#### Secrets Management
```python
# Django - ALWAYS use environment variables
import os
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')
ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
```

```typescript
// Next.js - ALWAYS use process.env
const apiUrl = process.env.DJANGO_API_URL  // Server-side only
const publicApiUrl = process.env.NEXT_PUBLIC_API_URL  // If client needs it
```

#### Authentication Flow
1. Credentials submitted via Next.js form over TLS
2. Next.js Server Action proxies to Django (hides API topology)
3. Django validates and issues session via **HttpOnly, Secure, SameSite=Lax cookie**
4. Token is **never accessible to JavaScript**
5. Internal users authenticate via **SSO (SAML 2.0 / OIDC)** - enforce MFA

```typescript
// Next.js cookie settings - REQUIRED pattern
cookies().set('session', token, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax',
  path: '/',
})
```

#### Database Access
```python
# ✅ CORRECT - Use ORM methods
User.objects.filter(email=email).first()
Application.objects.select_related('candidate', 'requisition').filter(status='active')
Candidate.objects.prefetch_related('experiences', 'education').all()

# ❌ FORBIDDEN - Raw SQL
User.objects.raw('SELECT * FROM users WHERE email = %s', [email])
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")  # SQL INJECTION!
```

#### Field-Level Encryption
```python
# REQUIRED for sensitive fields
from django_cryptography.fields import encrypt

class CandidateProfile(models.Model):
    phone = encrypt(models.CharField(max_length=20))  # Encrypted at rest
    ssn = encrypt(models.CharField(max_length=11, blank=True))  # If collected

class Offer(models.Model):
    base_salary = encrypt(models.DecimalField())  # Salary must be encrypted
```

---

## 3. Django Backend Rules

### Middleware Order (IMMUTABLE)
The order in `config/settings/base.py` MUST be:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',      # 1st - SSL/HSTS
    'django.middleware.cache.UpdateCacheMiddleware',      # 2nd
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',              # Before CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',          # Before auth
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.AuditLogMiddleware',            # Custom - logs all requests
    'apps.core.middleware.TenantMiddleware',              # If multi-tenancy added
]
```

### Required Security Settings
```python
# config/settings/production.py - PRODUCTION REQUIRED
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# CORS - only allow your Next.js frontends
CORS_ALLOWED_ORIGINS = [
    'https://careers.company.com',      # Public app
    'https://hire.company.com',         # Internal app
]
CORS_ALLOW_CREDENTIALS = True
```

### API Design Pattern
```python
# Every DRF view MUST include:
# 1. Explicit permission classes
# 2. Input validation via serializer
# 3. Service layer for business logic
# 4. Pagination for list endpoints
# 5. Filtering and search capabilities

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.core.permissions import HasPermission

class ApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasPermission('applications.view_application')]
    serializer_class = ApplicationSerializer
    filterset_class = ApplicationFilter
    search_fields = ['candidate__user__email', 'candidate__user__first_name']
    ordering_fields = ['applied_at', 'updated_at']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # ALWAYS optimize queries
        return Application.objects.select_related(
            'candidate__user',
            'requisition',
            'current_stage'
        ).prefetch_related(
            'tags',
            'events'
        ).filter(
            # RBAC: users only see applications they have permission to view
            requisition__department__in=self.request.user.accessible_departments
        )

    def perform_create(self, serializer):
        # Business logic in service layer, not in view
        ApplicationService.create_application(
            serializer.validated_data,
            user=self.request.user
        )
```

### Service Layer Pattern (REQUIRED)
```python
# apps/applications/services.py
# ALL business logic lives in services, not in views, serializers, or models

from django.db import transaction
from apps.core.services import BaseService

class ApplicationService(BaseService):
    @staticmethod
    @transaction.atomic
    def create_application(validated_data: dict, user) -> Application:
        """
        Creates a new application and triggers side effects.

        Business rules:
        - Prevent duplicate applications to same requisition
        - Auto-assign to first pipeline stage
        - Trigger welcome email
        - Log application event
        - Update requisition application count
        """
        candidate = validated_data['candidate']
        requisition = validated_data['requisition']

        # Check for duplicate
        if Application.objects.filter(
            candidate=candidate,
            requisition=requisition
        ).exists():
            raise ValidationError('Candidate has already applied to this position')

        # Create application
        application = Application.objects.create(
            **validated_data,
            current_stage=requisition.stages.first(),
            status='applied',
            source=validated_data.get('source', 'direct')
        )

        # Side effects
        ApplicationEventService.log_event(
            application=application,
            event_type='application.created',
            actor=user
        )

        NotificationService.send_application_confirmation(application)

        # Update metrics
        requisition.application_count = F('application_count') + 1
        requisition.save(update_fields=['application_count'])

        return application

    @staticmethod
    @transaction.atomic
    def move_to_stage(application: Application, stage: PipelineStage, actor) -> Application:
        """Move candidate to different pipeline stage with proper logging."""
        if application.current_stage == stage:
            return application

        old_stage = application.current_stage
        application.current_stage = stage
        application.save(update_fields=['current_stage', 'updated_at'])

        ApplicationEventService.log_event(
            application=application,
            event_type='application.stage_changed',
            actor=actor,
            metadata={'from_stage': old_stage.id, 'to_stage': stage.id}
        )

        # Trigger any auto-actions configured for this stage
        if stage.auto_actions:
            StageAutomationService.execute_actions(application, stage)

        return application
```

### Selector Pattern (Complex Queries)
```python
# apps/applications/selectors.py
# Complex database queries and aggregations live here

from django.db.models import Count, Q, Avg, F, Prefetch

class ApplicationSelector:
    @staticmethod
    def get_pipeline_board(requisition_id: int, user):
        """
        Returns optimized pipeline data for Kanban board.
        Includes all stages with candidate counts and candidates.
        """
        requisition = Requisition.objects.get(id=requisition_id)

        # Verify user has permission
        if not user.has_perm('applications.view_application', requisition):
            raise PermissionDenied()

        stages = requisition.stages.prefetch_related(
            Prefetch(
                'applications',
                queryset=Application.objects.select_related(
                    'candidate__user'
                ).prefetch_related(
                    'tags'
                ).filter(
                    status='active'
                ).order_by('-applied_at')
            )
        ).annotate(
            candidate_count=Count('applications', filter=Q(applications__status='active'))
        ).order_by('order')

        return stages

    @staticmethod
    def search_candidates(query: str, filters: dict, user):
        """
        Full-text search across candidates using Elasticsearch.
        Falls back to database ILIKE search if ES unavailable.
        """
        try:
            # Use Elasticsearch for semantic search
            return CandidateSearchService.search(query, filters, user)
        except ElasticsearchException:
            # Fallback to database search
            qs = CandidateProfile.objects.select_related('user').filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(user__email__icontains=query) |
                Q(resume_parsed__icontains=query)
            )

            # Apply filters
            if filters.get('skills'):
                qs = qs.filter(skills__name__in=filters['skills'])

            if filters.get('experience_min'):
                qs = qs.filter(years_experience__gte=filters['experience_min'])

            return qs.distinct()
```

---

## 4. Next.js Frontend Rules

### Dual Frontend Architecture

#### Public App (`apps/public-careers`)
- **Purpose:** SEO-optimized career site for candidates
- **Rendering:** Heavy SSR/SSG for job listings, Static Generation where possible
- **Auth:** Simple candidate authentication (email/password, social login)
- **State:** Minimal client state, prefer server components
- **Deployment:** CDN-friendly, aggressive caching

#### Internal App (`apps/internal-dashboard`)
- **Purpose:** Feature-rich recruiter/HR dashboard
- **Rendering:** Hybrid SSR + CSR, heavy client interactivity
- **Auth:** Enterprise SSO (SAML 2.0 / OIDC) with MFA enforcement
- **State:** Complex state management (Zustand for global state)
- **Deployment:** Behind auth, no public caching

### Server-Only Barrier
```typescript
// ANY file with sensitive logic MUST import this
import 'server-only'

// This causes build failure if accidentally imported in Client Component
```

### Server Actions - REQUIRED Pattern
```typescript
'use server'

import { z } from 'zod'
import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'

// 1. ALWAYS define schema with Zod
const CreateApplicationSchema = z.object({
  requisitionId: z.string().uuid(),
  coverLetter: z.string().max(5000).optional(),
  resumeFile: z.instanceof(File).optional(),
  screeningResponses: z.record(z.string(), z.any()),
})

export async function createApplication(formData: FormData) {
  // 2. ALWAYS verify session FIRST
  const session = await verifySession()
  if (!session?.user?.id) {
    throw new Error('Unauthorized')
  }

  // 3. ALWAYS validate input
  const validatedFields = CreateApplicationSchema.safeParse({
    requisitionId: formData.get('requisitionId'),
    coverLetter: formData.get('coverLetter'),
    resumeFile: formData.get('resume'),
    screeningResponses: JSON.parse(formData.get('screeningResponses') as string),
  })

  if (!validatedFields.success) {
    return {
      success: false,
      errors: validatedFields.error.flatten().fieldErrors
    }
  }

  // 4. Call Django API with validated data
  const response = await fetch(`${process.env.DJANGO_API_URL}/api/v1/applications/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.accessToken}`,
    },
    body: JSON.stringify(validatedFields.data),
  })

  if (!response.ok) {
    const error = await response.json()
    return { success: false, errors: error }
  }

  const application = await response.json()

  // 5. Revalidate cached data
  revalidatePath('/applications')

  return { success: true, data: application }
}
```

### Data Access Layer Pattern (DAL)
```typescript
// lib/dal.ts - ALL Django API calls go through here
import 'server-only'
import { cookies } from 'next/headers'

const API_URL = process.env.DJANGO_API_URL

async function getAuthHeaders() {
  const sessionCookie = cookies().get('session')
  if (!sessionCookie) {
    throw new Error('Unauthorized')
  }

  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${sessionCookie.value}`,
  }
}

export async function getJobs(params?: {
  department?: string
  location?: string
  search?: string
}) {
  const searchParams = new URLSearchParams(params as any)
  const res = await fetch(`${API_URL}/api/v1/jobs/?${searchParams}`, {
    headers: { 'Content-Type': 'application/json' },
    next: { revalidate: 300 }, // Cache for 5 minutes
  })

  if (!res.ok) throw new Error('Failed to fetch jobs')
  return res.json()
}

export async function getApplications() {
  const res = await fetch(`${API_URL}/api/v1/applications/`, {
    headers: await getAuthHeaders(),
    cache: 'no-store', // Always fresh for user-specific data
  })

  if (!res.ok) throw new Error('Failed to fetch applications')
  return res.json()
}

export async function getPipelineBoard(requisitionId: string) {
  const res = await fetch(
    `${API_URL}/api/v1/internal/requisitions/${requisitionId}/pipeline/`,
    {
      headers: await getAuthHeaders(),
      cache: 'no-store', // Real-time data
    }
  )

  if (!res.ok) throw new Error('Failed to fetch pipeline')
  return res.json()
}

// Components use DAL, never fetch directly
// ❌ WRONG: fetch() in component
// ✅ CORRECT: import { getJobs } from '@/lib/dal'
```

### RBAC in Next.js (Internal App Only)
```typescript
// lib/auth/permissions.ts
import 'server-only'
import { getSession } from '@/lib/auth/session'

export async function requirePermission(permission: string) {
  const session = await getSession()

  if (!session?.user) {
    throw new Error('Unauthorized')
  }

  if (!session.user.permissions?.includes(permission)) {
    throw new Error('Forbidden: Insufficient permissions')
  }

  return session.user
}

export async function hasPermission(permission: string): Promise<boolean> {
  const session = await getSession()
  return session?.user?.permissions?.includes(permission) ?? false
}

// Usage in Server Component
export default async function ApplicationsPage() {
  await requirePermission('applications.view_application')

  const applications = await getApplications()

  return <ApplicationsList applications={applications} />
}
```

### CSP with Nonces (Required for Production)
```typescript
// middleware.ts (both apps)
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')

  const cspHeader = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}' 'strict-dynamic' https://cdn.jsdelivr.net;
    style-src 'self' 'unsafe-inline';
    img-src 'self' blob: data: https://*.amazonaws.com;
    font-src 'self' data:;
    connect-src 'self' ${process.env.NEXT_PUBLIC_API_URL} ${process.env.NEXT_PUBLIC_WS_URL};
    frame-ancestors 'none';
    base-uri 'self';
    form-action 'self';
  `.replace(/\s{2,}/g, ' ').trim()

  const response = NextResponse.next()
  response.headers.set('Content-Security-Policy', cspHeader)
  response.headers.set('X-Nonce', nonce)
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')

  return response
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}
```

```typescript
// Pages using CSP MUST include:
export const dynamic = 'force-dynamic'  // Nonces require dynamic rendering
```

---

## 5. Type Safety & Integration

### Automated Type Generation
Use `drf-spectacular` to generate OpenAPI schema, then `openapi-typescript` to create TypeScript types:

```bash
# Generate OpenAPI schema from Django
python manage.py spectacular --file schema.yml

# Generate TypeScript types
npx openapi-typescript schema.yml --output apps/shared/types/api.ts

# Run this after ANY Django model or serializer change
npm run sync-types
```

### Type Contract Enforcement
```typescript
// apps/shared/types/api.ts - Auto-generated, DO NOT EDIT MANUALLY
export interface CandidateProfile {
  id: string
  user: {
    id: string
    email: string
    first_name: string
    last_name: string
  }
  phone: string
  location_city: string
  location_country: string
  resume_file: string | null
  created_at: string
  updated_at: string
}

export interface Application {
  id: string
  application_id: string
  candidate: CandidateProfile
  requisition: Requisition
  status: 'applied' | 'screening' | 'interview' | 'offer' | 'hired' | 'rejected'
  current_stage: PipelineStage
  applied_at: string
  updated_at: string
}

// All API responses MUST be typed
const applications: Application[] = await getApplications()
```

### Shared Component Library
```typescript
// apps/shared/components/ - Shared between public and internal apps
// Use TypeScript, Tailwind, and strict prop types

import { type VariantProps, cva } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        outline: 'border border-input hover:bg-accent',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
      },
      size: {
        sm: 'h-9 px-3 text-sm',
        md: 'h-10 px-4',
        lg: 'h-11 px-8 text-lg',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
)

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean
}

export function Button({
  className,
  variant,
  size,
  isLoading,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      disabled={isLoading || props.disabled}
      {...props}
    >
      {isLoading ? <Spinner className="mr-2" /> : null}
      {children}
    </button>
  )
}
```

---

## 6. Testing Requirements

### Every Feature MUST Have Tests

#### Django Tests
```python
# apps/applications/tests/test_services.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.applications.services import ApplicationService
from apps.applications.tests.factories import ApplicationFactory, RequisitionFactory

@pytest.mark.django_db
class TestApplicationService:
    def test_create_application_prevents_duplicates(self):
        """Candidates cannot apply twice to same requisition."""
        candidate = CandidateFactory()
        requisition = RequisitionFactory()

        # First application succeeds
        app1 = ApplicationService.create_application({
            'candidate': candidate,
            'requisition': requisition,
        }, user=candidate.user)

        assert app1.id is not None

        # Second application fails
        with pytest.raises(ValidationError, match='already applied'):
            ApplicationService.create_application({
                'candidate': candidate,
                'requisition': requisition,
            }, user=candidate.user)

    def test_move_to_stage_logs_event(self):
        """Stage transitions are logged in audit trail."""
        application = ApplicationFactory()
        new_stage = application.requisition.stages.all()[1]

        ApplicationService.move_to_stage(
            application,
            new_stage,
            actor=application.candidate.user
        )

        # Verify event was logged
        event = application.events.latest('created_at')
        assert event.event_type == 'application.stage_changed'
        assert event.metadata['to_stage'] == new_stage.id


@pytest.mark.django_db
class TestApplicationAPI:
    def test_create_application_requires_auth(self, client: APIClient):
        """Unauthenticated requests MUST be rejected."""
        requisition = RequisitionFactory()
        response = client.post(
            reverse('application-list'),
            {
                'requisition': str(requisition.id),
                'cover_letter': 'Test',
            }
        )
        assert response.status_code == 401

    def test_create_application_validates_input(self, authenticated_client: APIClient):
        """Invalid input MUST be rejected."""
        response = authenticated_client.post(
            reverse('application-list'),
            {'requisition': 'invalid-uuid'}
        )
        assert response.status_code == 400
        assert 'requisition' in response.json()

    def test_rbac_prevents_unauthorized_access(self, authenticated_client: APIClient):
        """Users cannot view applications outside their departments."""
        other_dept_application = ApplicationFactory(
            requisition__department__name='Engineering'
        )

        # User from HR department tries to access Engineering application
        response = authenticated_client.get(
            reverse('application-detail', args=[other_dept_application.id])
        )
        assert response.status_code == 403
```

#### Next.js Tests
```typescript
// apps/internal-dashboard/__tests__/actions/moveApplication.test.ts
import { moveApplicationToStage } from '@/app/actions/applications'
import { mockSession } from '@/tests/mocks/session'

// Mock Next.js cookies
jest.mock('next/headers', () => ({
  cookies: () => ({
    get: () => ({ value: 'mock-session-token' }),
  }),
}))

describe('moveApplicationToStage', () => {
  beforeEach(() => {
    fetchMock.resetMocks()
  })

  it('rejects unauthorized users', async () => {
    const formData = new FormData()
    formData.set('applicationId', '123')
    formData.set('stageId', '456')

    fetchMock.mockResponseOnce(JSON.stringify({ detail: 'Unauthorized' }), {
      status: 401
    })

    const result = await moveApplicationToStage(formData)

    expect(result.success).toBe(false)
    expect(result.error).toContain('Unauthorized')
  })

  it('validates required fields', async () => {
    const formData = new FormData()
    // Missing applicationId and stageId

    const result = await moveApplicationToStage(formData)

    expect(result.success).toBe(false)
    expect(result.errors).toBeDefined()
  })

  it('successfully moves application', async () => {
    const formData = new FormData()
    formData.set('applicationId', '123')
    formData.set('stageId', '456')

    fetchMock.mockResponseOnce(JSON.stringify({
      id: '123',
      current_stage: { id: '456', name: 'Interview' }
    }))

    const result = await moveApplicationToStage(formData)

    expect(result.success).toBe(true)
    expect(result.data.current_stage.id).toBe('456')
  })
})
```

#### E2E Tests (Playwright)
```typescript
// apps/internal-dashboard/e2e/application-pipeline.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Application Pipeline', () => {
  test.beforeEach(async ({ page }) => {
    // Login as recruiter
    await page.goto('/login')
    await page.fill('[name="email"]', 'recruiter@test.com')
    await page.fill('[name="password"]', 'password')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL('/dashboard')
  })

  test('drag and drop candidate between stages', async ({ page }) => {
    await page.goto('/requisitions/req-123/pipeline')

    // Wait for pipeline to load
    await page.waitForSelector('[data-testid="pipeline-board"]')

    // Drag candidate from "Applied" to "Screening"
    const candidate = page.locator('[data-candidate-id="candidate-123"]')
    const targetStage = page.locator('[data-stage="screening"]')

    await candidate.dragTo(targetStage)

    // Verify stage change
    await expect(page.locator('[data-candidate-id="candidate-123"]'))
      .toHaveAttribute('data-stage', 'screening')

    // Verify toast notification
    await expect(page.locator('[role="alert"]'))
      .toContainText('Candidate moved to Screening')
  })

  test('filters applications by status', async ({ page }) => {
    await page.goto('/applications')

    await page.selectOption('[name="status"]', 'interview')

    // Verify filtered results
    const applications = page.locator('[data-testid="application-row"]')
    await expect(applications).toHaveCount(5)

    for (const app of await applications.all()) {
      await expect(app).toContainText('Interview')
    }
  })
})
```

### Test Commands
```bash
# Django
pytest -v --cov=apps --cov-report=term-missing --cov-report=html
pytest apps/applications/tests/ -v  # Specific app

# Next.js Public
cd apps/public-careers
npm test
npm run test:coverage

# Next.js Internal
cd apps/internal-dashboard
npm test
npm run test:e2e  # Playwright E2E

# All tests
npm run test:all  # Root package.json script
```

---

## 7. Code Organization Rules

### File Size Limits
- **Maximum 300 lines per file** - Refactor if exceeding
- **Maximum 50 lines per function** - Extract to helper functions
- **Maximum 10 dependencies per module** - Split if more
- **Exception:** Auto-generated files (types, migrations)

### Directory Structure
```
hr_plus/
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── accounts/          # User models, auth, SSO
│   │   ├── candidates/        # Candidate profiles, resumes
│   │   ├── jobs/              # Requisitions, job postings
│   │   ├── applications/      # Applications, pipeline
│   │   ├── interviews/        # Scheduling, scorecards
│   │   ├── assessments/       # Tests, reference checks
│   │   ├── offers/            # Offer management
│   │   ├── onboarding/        # Pre-boarding
│   │   ├── communications/    # Email, notifications, messaging
│   │   ├── analytics/         # Dashboards, reports
│   │   ├── integrations/      # External system connectors
│   │   ├── compliance/        # GDPR, EEO, audit
│   │   └── core/              # Shared utilities, base models, permissions
│   │       ├── models.py      # Abstract base models
│   │       ├── permissions.py # RBAC helpers
│   │       ├── services.py    # Base service class
│   │       ├── middleware.py  # Custom middleware
│   │       └── utils.py
│   ├── tasks/                 # Celery tasks
│   ├── tests/                 # Integration tests
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   └── manage.py
│
├── apps/
│   ├── public-careers/        # Public-facing career site
│   │   ├── app/
│   │   │   ├── (public)/
│   │   │   │   ├── jobs/
│   │   │   │   │   ├── page.tsx
│   │   │   │   │   └── [slug]/
│   │   │   │   │       └── page.tsx
│   │   │   │   ├── about/
│   │   │   │   └── culture/
│   │   │   ├── (auth)/
│   │   │   │   ├── login/
│   │   │   │   ├── register/
│   │   │   │   └── apply/
│   │   │   │       └── [jobId]/
│   │   │   ├── dashboard/     # Candidate dashboard
│   │   │   │   ├── applications/
│   │   │   │   ├── profile/
│   │   │   │   └── interviews/
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── ui/            # Reusable primitives
│   │   │   ├── features/      # Feature-specific components
│   │   │   │   ├── job-search/
│   │   │   │   ├── application-form/
│   │   │   │   └── profile-builder/
│   │   │   └── layouts/
│   │   ├── lib/
│   │   │   ├── dal.ts         # Data Access Layer
│   │   │   ├── auth.ts        # Auth utilities
│   │   │   └── utils.ts
│   │   ├── types/
│   │   │   └── api.ts         # Auto-generated types
│   │   ├── __tests__/
│   │   └── package.json
│   │
│   ├── internal-dashboard/    # Internal staff dashboard
│   │   ├── app/
│   │   │   ├── (dashboard)/
│   │   │   │   ├── dashboard/
│   │   │   │   ├── requisitions/
│   │   │   │   │   ├── page.tsx
│   │   │   │   │   └── [id]/
│   │   │   │   │       ├── page.tsx
│   │   │   │   │       └── pipeline/
│   │   │   │   ├── applications/
│   │   │   │   ├── candidates/
│   │   │   │   ├── interviews/
│   │   │   │   ├── offers/
│   │   │   │   ├── analytics/
│   │   │   │   └── settings/
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── ui/            # shadcn/ui components
│   │   │   ├── features/
│   │   │   │   ├── pipeline-board/
│   │   │   │   ├── candidate-search/
│   │   │   │   ├── interview-scheduler/
│   │   │   │   └── analytics-charts/
│   │   │   └── layouts/
│   │   ├── lib/
│   │   │   ├── dal.ts
│   │   │   ├── auth/
│   │   │   │   ├── session.ts
│   │   │   │   ├── permissions.ts
│   │   │   │   └── sso.ts
│   │   │   └── state/         # Zustand stores
│   │   ├── types/
│   │   │   └── api.ts
│   │   ├── __tests__/
│   │   ├── e2e/
│   │   └── package.json
│   │
│   └── shared/                # Shared code between apps
│       ├── components/        # Shared UI components
│       ├── types/             # Shared types
│       ├── utils/             # Shared utilities
│       └── package.json
│
├── docker/
│   ├── django/
│   │   └── Dockerfile
│   ├── nextjs-public/
│   │   └── Dockerfile
│   └── nextjs-internal/
│       └── Dockerfile
│
├── docker-compose.yml
├── docker-compose.prod.yml
└── package.json               # Root monorepo manager
```

### Django App Structure (Standard)
```
apps/applications/
├── __init__.py
├── models.py          # Data models only - no business logic
├── serializers.py     # Input/output validation and serialization
├── views.py           # HTTP handling - delegates to services
├── services.py        # ⭐ Business logic HERE
├── selectors.py       # ⭐ Complex queries HERE
├── filters.py         # django-filter FilterSets
├── permissions.py     # Custom permission classes
├── signals.py         # Django signals (use sparingly)
├── admin.py           # Django admin customization
├── urls.py            # URL routing
├── apps.py            # App configuration
├── tasks.py           # Celery tasks
├── migrations/
└── tests/
    ├── __init__.py
    ├── factories.py   # Factory Boy factories
    ├── test_models.py
    ├── test_services.py
    ├── test_selectors.py
    ├── test_views.py
    └── test_tasks.py
```

---

## 8. Git & Workflow Rules

### Branch Strategy
```
main            - Production-ready code only
├── develop     - Integration branch
├── staging     - Pre-production testing
└── feature/*   - Individual features
└── hotfix/*    - Production hotfixes
```

### Commit Convention
```bash
# Format: type(scope): description

# Types: feat, fix, refactor, test, docs, chore, perf, style

# Backend examples
feat(applications): add duplicate detection on submission
fix(auth): resolve SSO token refresh issue
test(interviews): add scorecard submission tests
refactor(candidates): extract resume parsing to service
perf(search): optimize Elasticsearch queries with filters

# Frontend examples
feat(pipeline): implement drag-and-drop stage transitions
fix(forms): prevent double submission on slow networks
test(auth): add E2E tests for SSO flow
docs(readme): update deployment instructions

# Infrastructure
chore(docker): update Postgres to 16.2
ci(github): add security scanning workflow
```

### Before Merging Checklist
- [ ] All tests pass (`pytest` + `npm test` in both apps)
- [ ] No linting errors (`ruff check` + `npm run lint`)
- [ ] Types are synced (regenerate if Django models/serializers changed)
- [ ] Security settings verified in production config
- [ ] Database migrations created and tested
- [ ] No console.log or debugging code left in
- [ ] API endpoints documented in OpenAPI schema
- [ ] Sensitive data not committed (check .env.example, not .env)
- [ ] Code reviewed by at least one team member
- [ ] Squash messy WIP commits

---

## 9. Forbidden Patterns

### Django Anti-Patterns
```python
# ❌ Logic in views - move to services
class ApplicationViewSet(viewsets.ModelViewSet):
    def create(self, request):
        # 100 lines of business logic here...  # WRONG
        # Check duplicates, send emails, log events...
        # This should all be in ApplicationService

# ❌ Logic in serializers
class ApplicationSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        # Complex business logic here...  # WRONG
        # Serializers should only handle data transformation

# ❌ Logic in models (beyond simple computed properties)
class Application(models.Model):
    def move_to_stage(self, stage):
        # Complex workflow logic...  # WRONG
        # This belongs in ApplicationService

# ❌ N+1 queries
for application in Application.objects.all():
    print(application.candidate.user.email)  # Query per iteration!
    print(application.requisition.title)      # Another query!

# ✅ Use select_related/prefetch_related
Application.objects.select_related(
    'candidate__user',
    'requisition'
).all()

# ❌ Unoptimized pagination
applications = Application.objects.all()[:1000]  # Loads all 1000 into memory

# ✅ Use Django pagination
from django.core.paginator import Paginator
paginator = Paginator(Application.objects.all(), 50)

# ❌ Missing permission checks
@api_view(['GET'])
def get_candidate_data(request, candidate_id):
    candidate = Candidate.objects.get(id=candidate_id)
    return Response(CandidateSerializer(candidate).data)  # Anyone can view!

# ✅ Always check permissions
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasPermission('candidates.view_candidate')])
def get_candidate_data(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    # Additional RBAC check
    if not request.user.can_view_candidate(candidate):
        raise PermissionDenied()
    return Response(CandidateSerializer(candidate).data)
```

### Next.js Anti-Patterns
```typescript
// ❌ Fetching in Client Components
'use client'
export function ApplicationList() {
  const [applications, setApplications] = useState([])
  useEffect(() => {
    fetch('/api/applications').then(...)  // WRONG - use Server Components
  }, [])
}

// ✅ Use Server Components
export default async function ApplicationList() {
  const applications = await getApplications()  // Server-side fetch
  return <ApplicationTable applications={applications} />
}

// ❌ Direct database access from Next.js
import { prisma } from '@/lib/db'  // FORBIDDEN - Django is the only DB gateway

// ❌ Secrets in client code
const API_KEY = 'sk-1234...'  // NEVER - use server-side env vars

// ❌ Business logic in frontend
'use client'
function ApplicationForm() {
  const handleSubmit = (data) => {
    // Validate duplicate application
    if (applications.some(app => app.requisitionId === data.requisitionId)) {
      // WRONG - this logic belongs in Django
      alert('Already applied')
      return
    }
  }
}

// ✅ Validation happens in Django, frontend just displays errors
async function submitApplication(formData: FormData) {
  'use server'
  const result = await fetch(`${API_URL}/api/v1/applications/`, {
    method: 'POST',
    body: JSON.stringify(formData),
  })
  // Django returns error if duplicate
  return result.json()
}

// ❌ Storing auth tokens in localStorage
localStorage.setItem('token', token)  // NEVER - vulnerable to XSS

// ✅ Use HttpOnly cookies set by Django
// Tokens are never accessible to JavaScript

// ❌ Missing permission checks in Server Actions
export async function deleteApplication(id: string) {
  // No auth check!
  await fetch(`${API_URL}/api/v1/applications/${id}/`, { method: 'DELETE' })
}

// ✅ Always verify permissions
export async function deleteApplication(id: string) {
  'use server'
  const user = await requirePermission('applications.delete_application')

  const response = await fetch(
    `${API_URL}/api/v1/applications/${id}/`,
    {
      method: 'DELETE',
      headers: await getAuthHeaders(),
    }
  )

  if (!response.ok) throw new Error('Failed to delete')
  revalidatePath('/applications')
}
```

---

## 10. AI Interaction Rules

### Plan Before Execute
1. **Never start coding immediately** - always outline the plan first
2. **Propose changes** before implementing
3. **Human approves architecture** before code generation
4. **For multi-file changes**, list all files that will be modified
5. **For new features**, confirm RBAC permissions and security implications

### Context Isolation
- When working on Django: provide only Python/Django context
- When working on Next.js: specify which app (public vs internal) and provide only TypeScript/React context
- When working across stack: break into separate tasks (Django first, then frontend)
- Keep context focused to reduce hallucinations

### Review Requirements
After generating code, always:
1. Run linters: `ruff check .` (Python), `npm run lint` (TypeScript)
2. Run type checks: `mypy apps/` (Python), `npm run type-check` (TypeScript)
3. Run tests: `pytest`, `npm test`
4. Verify security patterns match this document
5. Check that business logic is in Django services, not Next.js
6. Verify RBAC permissions are enforced
7. Ensure no PII is logged or exposed inappropriately

### Restricted Files
These files require **explicit human approval** for any changes:
- `config/settings/*.py` (Django settings)
- `middleware.ts` (Next.js middleware in both apps)
- Any file in `apps/accounts/` or `apps/compliance/` (auth and compliance)
- `.env*` files (never commit with real secrets)
- `requirements/*.txt` / `package.json` (dependency changes)
- `docker-compose*.yml` (infrastructure)
- RBAC permission definitions
- Encryption key handling code

---

## 11. Dependency Management

### Package Verification
Before installing any package:
1. Verify package exists on official registry (PyPI/npm)
2. Check for typosquatting (similar names to popular packages)
3. Review package permissions/scripts
4. Prefer packages with 1000+ weekly downloads and recent maintenance
5. Check for known vulnerabilities (`pip-audit`, `npm audit`)

### Python Dependencies
```bash
# Use separate requirement files
requirements/
├── base.txt           # Core dependencies
├── development.txt    # Dev tools (includes base.txt)
└── production.txt     # Production-only (includes base.txt)

# Pin exact versions in production
Django==5.0.2
djangorestframework==3.14.0
celery==5.3.4

# Always commit lockfiles
pip freeze > requirements/production.txt

# Install in production
pip install -r requirements/production.txt --no-deps  # Enforce exact versions
```

### Node Dependencies
```bash
# Always commit lockfiles
package-lock.json  # npm
yarn.lock          # yarn
pnpm-lock.yaml     # pnpm

# Install in production
npm ci  # NOT npm install - ensures exact versions from lockfile
```

### Monorepo Dependency Management
```json
// Root package.json
{
  "name": "hr-plus-monorepo",
  "private": true,
  "workspaces": [
    "apps/public-careers",
    "apps/internal-dashboard",
    "apps/shared"
  ],
  "scripts": {
    "dev:public": "npm run dev --workspace=apps/public-careers",
    "dev:internal": "npm run dev --workspace=apps/internal-dashboard",
    "build:all": "npm run build --workspaces",
    "test:all": "npm run test --workspaces",
    "lint:all": "npm run lint --workspaces",
    "type-check:all": "npm run type-check --workspaces"
  }
}
```

---

## 12. Error Handling Standards

### Django Error Responses
```python
# apps/core/exceptions.py
from rest_framework.exceptions import APIException

class BusinessValidationError(APIException):
    status_code = 400
    default_detail = 'Business validation failed'
    default_code = 'business_validation_error'

class DuplicateApplicationError(BusinessValidationError):
    default_detail = 'You have already applied to this position'
    default_code = 'duplicate_application'

class InsufficientPermissionError(APIException):
    status_code = 403
    default_detail = 'You do not have permission to perform this action'
    default_code = 'insufficient_permission'

# Use in services
def create_application(candidate, requisition):
    if Application.objects.filter(
        candidate=candidate,
        requisition=requisition
    ).exists():
        raise DuplicateApplicationError()

    # ... rest of logic
```

### Next.js Error Boundaries
```typescript
// app/error.tsx (both apps) - REQUIRED
'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log error to monitoring service
    console.error('Application error:', error)
  }, [error])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <h2 className="text-2xl font-bold">Something went wrong</h2>
      <p className="mt-2 text-gray-600">
        {error.message || 'An unexpected error occurred'}
      </p>
      <Button onClick={reset} className="mt-4">
        Try again
      </Button>
    </div>
  )
}

// app/global-error.tsx - Catches errors in root layout
'use client'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html>
      <body>
        <h2>Something went wrong!</h2>
        <button onClick={reset}>Try again</button>
      </body>
    </html>
  )
}
```

### Graceful Degradation
```typescript
// lib/dal.ts - Fallback for service failures
export async function getJobs(params?: JobSearchParams) {
  try {
    const res = await fetch(`${API_URL}/api/v1/jobs/?${new URLSearchParams(params)}`, {
      next: { revalidate: 300 },
    })

    if (!res.ok) throw new Error('Failed to fetch jobs')
    return res.json()
  } catch (error) {
    // Log to monitoring
    console.error('Job fetch failed:', error)

    // Return cached fallback or empty state
    // Don't crash the entire page
    return { results: [], count: 0 }
  }
}
```

---

## 13. Performance Optimization

### Django Query Optimization
```python
# ✅ ALWAYS use select_related for foreign keys
Application.objects.select_related(
    'candidate__user',
    'requisition__department',
    'current_stage'
)

# ✅ ALWAYS use prefetch_related for many-to-many and reverse foreign keys
Application.objects.prefetch_related(
    'tags',
    'events__actor',
    'interviews__participants'
)

# ✅ Use only() and defer() to limit fields
Application.objects.only('id', 'status', 'applied_at')  # Only these fields
Application.objects.defer('cover_letter', 'screening_responses')  # All except these

# ✅ Use pagination for large datasets
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

# ✅ Use database indexes on frequently queried fields
class Application(models.Model):
    status = models.CharField(max_length=20, db_index=True)
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['requisition', 'status']),
            models.Index(fields=['candidate', '-applied_at']),
        ]

# ✅ Use QuerySet annotations for computed values
from django.db.models import Count, Avg

Requisition.objects.annotate(
    application_count=Count('applications'),
    avg_days_to_fill=Avg('filled_applications__days_to_fill')
)
```

### Next.js Optimization
```typescript
// ✅ Use proper caching strategies
// Static data - cache indefinitely
export async function getJobCategories() {
  const res = await fetch(`${API_URL}/api/v1/jobs/categories/`, {
    next: { revalidate: false },  // Cache forever
  })
  return res.json()
}

// Semi-static data - revalidate periodically
export async function getJobs() {
  const res = await fetch(`${API_URL}/api/v1/jobs/`, {
    next: { revalidate: 300 },  // 5 minutes
  })
  return res.json()
}

// Dynamic user data - never cache
export async function getMyApplications() {
  const res = await fetch(`${API_URL}/api/v1/applications/`, {
    cache: 'no-store',
  })
  return res.json()
}

// ✅ Use React Query for client-side caching (internal app)
'use client'
import { useQuery } from '@tanstack/react-query'

export function useApplications(requisitionId: string) {
  return useQuery({
    queryKey: ['applications', requisitionId],
    queryFn: () => fetchApplications(requisitionId),
    staleTime: 30_000,  // 30 seconds
    refetchInterval: 60_000,  // Refetch every minute
  })
}

// ✅ Implement virtual scrolling for large lists (pipeline board)
import { useVirtualizer } from '@tanstack/react-virtual'

export function PipelineColumn({ applications }: { applications: Application[] }) {
  const parentRef = React.useRef<HTMLDivElement>(null)

  const rowVirtualizer = useVirtualizer({
    count: applications.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100,  // Estimated row height
  })

  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      <div style={{ height: `${rowVirtualizer.getTotalSize()}px` }}>
        {rowVirtualizer.getVirtualItems().map((virtualRow) => (
          <ApplicationCard
            key={applications[virtualRow.index].id}
            application={applications[virtualRow.index]}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualRow.size}px`,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          />
        ))}
      </div>
    </div>
  )
}

// ✅ Use dynamic imports for code splitting
const PipelineBoard = dynamic(() => import('@/components/features/pipeline-board'), {
  loading: () => <PipelineLoadingSkeleton />,
  ssr: false,  // Only load on client if needed
})

// ✅ Optimize images
import Image from 'next/image'

<Image
  src={candidate.photo_url}
  alt={candidate.name}
  width={48}
  height={48}
  className="rounded-full"
  loading="lazy"  // Lazy load
  placeholder="blur"  // Show blur while loading
  blurDataURL={candidate.photo_blur}
/>
```

### Caching Strategy
```python
# Django - Redis caching
from django.core.cache import cache

class JobSelector:
    @staticmethod
    def get_active_jobs():
        # Cache for 5 minutes
        cache_key = 'jobs:active'
        cached = cache.get(cache_key)

        if cached is not None:
            return cached

        jobs = Job.objects.filter(
            status='open',
            published_at__lte=timezone.now()
        ).select_related('department', 'location')

        cache.set(cache_key, jobs, timeout=300)
        return jobs

    @staticmethod
    def invalidate_job_cache():
        """Call this when jobs are created/updated."""
        cache.delete('jobs:active')
```

---

## 14. Compliance & Audit Requirements

### Audit Logging (MANDATORY)
```python
# ALL data access and modifications MUST be logged

# apps/core/middleware.py
class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Log all API requests (except health checks)
        if request.path.startswith('/api/') and request.path != '/api/health/':
            AuditLog.objects.create(
                actor=request.user if request.user.is_authenticated else None,
                actor_ip=get_client_ip(request),
                action=request.method,
                resource_type='api',
                resource_id=request.path,
                metadata={
                    'user_agent': request.META.get('HTTP_USER_AGENT'),
                    'status_code': response.status_code,
                }
            )

        return response

# apps/compliance/models.py
class AuditLog(models.Model):
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    actor_ip = models.GenericIPAddressField(null=True)
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=255)
    changes = models.JSONField(null=True)  # Before/after for updates
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['actor', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['-timestamp']),
        ]
        # Audit logs are append-only
        permissions = [
            ('view_auditlog', 'Can view audit logs'),
        ]
```

### GDPR Compliance
```python
# apps/compliance/services.py

class GDPRService:
    @staticmethod
    def export_candidate_data(candidate: CandidateProfile) -> dict:
        """
        Export all data for a candidate (GDPR Right to Access).
        Returns machine-readable JSON.
        """
        return {
            'profile': CandidateSerializer(candidate).data,
            'applications': ApplicationSerializer(
                candidate.applications.all(), many=True
            ).data,
            'communications': EmailLogSerializer(
                EmailLog.objects.filter(recipient_email=candidate.user.email),
                many=True
            ).data,
            'audit_trail': AuditLogSerializer(
                AuditLog.objects.filter(actor=candidate.user),
                many=True
            ).data,
            'exported_at': timezone.now().isoformat(),
        }

    @staticmethod
    @transaction.atomic
    def anonymize_candidate(candidate: CandidateProfile, reason: str):
        """
        Anonymize candidate data (GDPR Right to Erasure).
        Removes PII while preserving aggregate statistics.
        """
        # Log before anonymization
        AuditLog.objects.create(
            actor=None,
            action='anonymize',
            resource_type='candidate',
            resource_id=str(candidate.id),
            metadata={'reason': reason}
        )

        # Anonymize user data
        user = candidate.user
        user.email = f'deleted_{user.id}@anonymized.local'
        user.first_name = 'Deleted'
        user.last_name = 'User'
        user.is_active = False
        user.save()

        # Anonymize candidate profile
        candidate.phone = ''
        candidate.linkedin_url = ''
        candidate.portfolio_url = ''
        candidate.resume_file.delete()  # Delete file from storage
        candidate.resume_parsed = {}
        candidate.save()

        # Anonymize applications
        for app in candidate.applications.all():
            app.cover_letter = ''
            app.screening_responses = {}
            app.save()

        # Create anonymization record
        AnonymizationRecord.objects.create(
            candidate_id=candidate.id,
            anonymized_at=timezone.now(),
            reason=reason
        )
```

### EEO Compliance
```python
# apps/compliance/models.py

class EEOData(models.Model):
    """
    Voluntary self-identification data.
    CRITICAL: This data MUST be stored separately from application data
    and NEVER shown to hiring team.
    """
    candidate = models.OneToOneField(CandidateProfile, on_delete=models.CASCADE)

    # Encrypted fields
    gender = encrypt(models.CharField(max_length=50, blank=True))
    race_ethnicity = encrypt(models.CharField(max_length=100, blank=True))
    veteran_status = encrypt(models.CharField(max_length=50, blank=True))
    disability_status = encrypt(models.CharField(max_length=50, blank=True))

    collected_at = models.DateTimeField(auto_now_add=True)
    consent_given = models.BooleanField(default=True)

    class Meta:
        # Only compliance admins can access
        permissions = [
            ('view_eeodata', 'Can view EEO data (compliance only)'),
        ]

    @staticmethod
    def generate_eeo_report(date_range: tuple):
        """
        Generate anonymized EEO-1 report.
        NO individual data is included, only aggregates.
        """
        # Implementation that returns only aggregate counts
        pass
```

---

## 15. Deployment & Infrastructure

### Environment Variables
```bash
# .env.example - COMMIT THIS
# .env - DO NOT COMMIT

# Django
DJANGO_SECRET_KEY=generate-with-django-secret-key-generator
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=api.hrplus.com,hire.company.com

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/hrplus
DB_POOL_SIZE=20

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# AWS
AWS_ACCESS_KEY_ID=your-key-id
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=hrplus-uploads
AWS_S3_REGION_NAME=us-east-1

# Email
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key

# SSO (Internal)
SAML_IDP_URL=https://sso.company.com
SAML_ENTITY_ID=hrplus-production
SAML_CERTIFICATE=path/to/cert.pem

# Monitoring
SENTRY_DSN=https://your-sentry-dsn

# Next.js (Public App)
NEXT_PUBLIC_API_URL=https://api.hrplus.com
NEXT_PUBLIC_WS_URL=wss://api.hrplus.com
DJANGO_API_URL=https://api.hrplus.com  # Server-side only

# Next.js (Internal App)
NEXT_PUBLIC_API_URL=https://api.hrplus.com
NEXT_PUBLIC_WS_URL=wss://api.hrplus.com
DJANGO_API_URL=https://api.hrplus.com
```

### Docker Deployment
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: hrplus
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - es_data:/usr/share/elasticsearch/data
    restart: unless-stopped

  django:
    build:
      context: ./backend
      dockerfile: ../docker/django/Dockerfile
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - ELASTICSEARCH_URL=${ELASTICSEARCH_URL}
    depends_on:
      - postgres
      - redis
      - elasticsearch
    restart: unless-stopped

  celery:
    build:
      context: ./backend
      dockerfile: ../docker/django/Dockerfile
    command: celery -A config worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  celery-beat:
    build:
      context: ./backend
      dockerfile: ../docker/django/Dockerfile
    command: celery -A config beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  public-app:
    build:
      context: ./apps/public-careers
      dockerfile: ../../docker/nextjs-public/Dockerfile
    environment:
      - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
      - DJANGO_API_URL=${DJANGO_API_URL}
    ports:
      - "3000:3000"
    restart: unless-stopped

  internal-app:
    build:
      context: ./apps/internal-dashboard
      dockerfile: ../../docker/nextjs-internal/Dockerfile
    environment:
      - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
      - DJANGO_API_URL=${DJANGO_API_URL}
    ports:
      - "3001:3000"
    restart: unless-stopped

volumes:
  postgres_data:
  es_data:
```

---

## Quick Reference Commands

```bash
# Development
docker compose up -d                    # Start all services
cd backend && python manage.py runserver  # Django dev
cd apps/public-careers && npm run dev   # Public app dev
cd apps/internal-dashboard && npm run dev  # Internal app dev

# Database
python manage.py makemigrations         # Create migrations
python manage.py migrate                # Apply migrations
python manage.py createsuperuser        # Create admin user

# Testing
pytest -v --cov=apps --cov-report=html  # Django tests with coverage
cd apps/public-careers && npm test      # Public app tests
cd apps/internal-dashboard && npm test  # Internal app tests
cd apps/internal-dashboard && npm run test:e2e  # E2E tests

# Linting & Formatting
ruff check --fix backend/               # Python lint
ruff format backend/                    # Python format
npm run lint --workspaces               # All Next.js apps lint
npm run format --workspaces             # All Next.js apps format

# Type Checking
mypy backend/apps/                      # Python types
npm run type-check --workspaces         # TypeScript types

# Type Generation
python manage.py spectacular --file schema.yml  # Generate OpenAPI
npx openapi-typescript schema.yml -o apps/shared/types/api.ts  # Generate TS types
npm run sync-types                      # Combined command

# Security
pip-audit                               # Python dependency audit
npm audit --workspaces                  # Node dependency audit
bandit -r backend/apps/                 # Python security scan
npm run audit:fix --workspaces          # Fix npm vulnerabilities

# Celery
celery -A config worker -l info         # Start worker
celery -A config beat -l info           # Start scheduler
celery -A config flower                 # Monitoring UI

# Production Build
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Monitoring
docker compose logs -f django           # Django logs
docker compose logs -f celery           # Celery logs
docker compose logs -f public-app       # Public app logs
docker compose logs -f internal-app     # Internal app logs
```

---

**Remember: You are an architect, security engineer, and auditor—not just a coder.**

**Focus distribution:**
- 40% Architecture & planning
- 30% Security & compliance
- 20% Testing & validation
- 10% Code generation

**Before writing any code, ask:**
1. Where does this logic belong? (Django service vs Next.js)
2. What permissions are required?
3. What could go wrong? (security, performance, data integrity)
4. How will this be tested?
5. Does this expose any PII or sensitive data?
6. Is this GDPR/EEO compliant?
