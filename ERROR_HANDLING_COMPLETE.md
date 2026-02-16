# Error Handling - Implementation Complete ✅

## Overview

Comprehensive error handling system has been implemented across the HR-Plus internal dashboard with improved error pages, centralized error utilities, enhanced logging, and standardized error handling patterns for Server Actions and API calls.

---

## Features Implemented

### 1. Error Handler Utilities ✅

**File:** [src/lib/errors/error-handler.ts](apps/internal-dashboard/src/lib/errors/error-handler.ts)

**Custom Error Classes:**
- `AppError` - Base application error
- `ValidationError` - Input validation errors (400)
- `AuthenticationError` - Authentication required errors (401)
- `AuthorizationError` - Permission denied errors (403)
- `NotFoundError` - Resource not found errors (404)
- `ServerError` - Internal server errors (500)

**Error Utilities:**
- `parseApiError(error)` - Parse API responses into user-friendly messages
- `logError(error, context)` - Log errors to monitoring service (Sentry-ready)
- `handleServerActionError(action, errorMessage)` - Async error handler for Server Actions
- `formatZodError(error)` - Extract validation errors from Zod
- `isRedirectError(error)` - Check if error is a Next.js redirect
- `retryWithBackoff(fn, maxRetries, baseDelay)` - Retry with exponential backoff

**Example Usage:**
```typescript
import { parseApiError, logError, ValidationError } from '@/lib/errors'

try {
  const data = await fetchData()
} catch (error) {
  logError(error as Error, { context: 'data-fetch' })
  const message = parseApiError(error)
  return { error: message }
}
```

---

### 2. API Client with Error Handling ✅

**File:** [src/lib/errors/api-client.ts](apps/internal-dashboard/src/lib/errors/api-client.ts)

**Features:**
- Centralized API client for all Django API calls
- Automatic authentication header injection
- Response parsing (JSON, text, no-content)
- HTTP status code handling
- Network error detection
- Automatic error logging
- Retry support with exponential backoff
- Cache control and revalidation

**API Methods:**
```typescript
import { api } from '@/lib/errors/api-client'

// GET request
const users = await api.get('/api/v1/users/')

// POST request
const newUser = await api.post('/api/v1/users/', {
  email: 'test@example.com',
  name: 'Test User',
})

// PUT request
const updated = await api.put('/api/v1/users/123/', { name: 'Updated Name' })

// DELETE request
await api.delete('/api/v1/users/123/')

// With retry
const data = await api.get('/api/v1/data/', { retries: 3 })

// With cache revalidation
const jobs = await api.get('/api/v1/jobs/', { revalidate: 300 }) // 5 minutes
```

**Error Handling:**
- Automatically parses error responses
- Logs errors with context
- Throws `ApiError` with status code and details
- Handles network failures gracefully

---

### 3. Server Action Wrappers ✅

**File:** [src/lib/errors/server-action-wrapper.ts](apps/internal-dashboard/src/lib/errors/server-action-wrapper.ts)

**Action Wrapper:**
Standardized wrapper for Server Actions with automatic validation and error handling.

```typescript
import { actionWrapper } from '@/lib/errors'
import { z } from 'zod'

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2),
})

export const createUser = actionWrapper({
  schema: CreateUserSchema,
  action: async (data) => {
    const user = await api.post('/api/v1/users/', data)
    revalidatePath('/users')
    return user
  },
  errorMessage: 'Failed to create user',
  logContext: { action: 'create-user' },
})

// Usage
const result = await createUser({ email: 'test@example.com', name: 'Test' })
if (result.success) {
  console.log('User created:', result.data)
} else {
  console.error('Error:', result.error)
  console.error('Field errors:', result.fields)
}
```

**Form Action Wrapper:**
Compatible with `useActionState` for form submissions.

```typescript
import { formActionWrapper } from '@/lib/errors'

export const createUserAction = formActionWrapper({
  schema: CreateUserSchema,
  transformFormData: (formData) => ({
    email: formData.get('email') as string,
    name: formData.get('name') as string,
  }),
  action: async (data) => {
    const user = await api.post('/api/v1/users/', data)
    redirect(`/users/${user.id}`)
  },
  errorMessage: 'Failed to create user',
})

// Usage in component
const [state, formAction, isPending] = useActionState(createUserAction, null)
```

**Return Type:**
```typescript
type ActionResult<T> =
  | { success: true; data: T }
  | { success: false; error: string; fields?: Record<string, string[]> }
```

---

### 4. Error Boundary Component ✅

**File:** [src/components/error/error-boundary.tsx](apps/internal-dashboard/src/components/error/error-boundary.tsx)

**Features:**
- Catches React component errors
- Displays user-friendly error UI
- Logs errors to monitoring service
- Shows error details in development
- Provides "Try Again" and "Go to Dashboard" actions
- Custom fallback UI support
- Error reset callback

**Usage:**
```typescript
import { ErrorBoundary } from '@/components/error/error-boundary'

export default function Page() {
  return (
    <ErrorBoundary onReset={() => console.log('Error cleared')}>
      <ComponentThatMightError />
    </ErrorBoundary>
  )
}

// With custom fallback
<ErrorBoundary fallback={<CustomErrorUI />}>
  <ComponentThatMightError />
</ErrorBoundary>
```

---

### 5. Error Message Components ✅

**File:** [src/components/error/error-message.tsx](apps/internal-dashboard/src/components/error/error-message.tsx)

**ErrorMessage Component:**
```typescript
import { ErrorMessage } from '@/components/error/error-message'

<ErrorMessage message="Failed to load data" type="error" />
<ErrorMessage message="This action requires approval" type="warning" />
<ErrorMessage message="Profile updated successfully" type="info" />
```

**FieldError Component:**
For form field validation errors.

```typescript
import { FieldError } from '@/components/error/error-message'

<div>
  <input name="email" />
  <FieldError error={errors.email} />
</div>

// With array of errors
<FieldError error={['Email is required', 'Email must be valid']} />
```

---

### 6. Improved Error Pages ✅

#### Root Error Page
**File:** [src/app/error.tsx](apps/internal-dashboard/src/app/error.tsx)

**Features:**
- Card-based error UI with icon
- Error ID display (digest)
- User-friendly error message
- Development mode: Stack trace
- "Try Again" and "Dashboard" actions
- Automatic error logging

#### Global Error Page
**File:** [src/app/global-error.tsx](apps/internal-dashboard/src/app/global-error.tsx)

**Features:**
- Catches critical app-wide errors
- Inline styled components (no CSS dependencies)
- Error ID display
- "Try Again" and "Reload Page" actions
- Automatic logging with critical flag

#### 404 Not Found Page
**File:** [src/app/not-found.tsx](apps/internal-dashboard/src/app/not-found.tsx)

**Features:**
- Large 404 display
- User-friendly message
- "Go to Dashboard" action
- Clean, centered card design

---

## Error Handling Patterns

### API Error Handling

**Before:**
```typescript
try {
  const response = await fetch('/api/endpoint')
  if (!response.ok) {
    throw new Error('Failed')
  }
  const data = await response.json()
  return data
} catch (error) {
  console.error(error)
  return null
}
```

**After:**
```typescript
import { api } from '@/lib/errors/api-client'

try {
  const data = await api.get('/api/endpoint')
  return data
} catch (error) {
  // Error automatically logged with context
  // User-friendly message automatically parsed
  const message = parseApiError(error)
  return { error: message }
}
```

### Server Action Error Handling

**Before:**
```typescript
export async function createItem(formData: FormData) {
  try {
    const response = await fetch('/api/items/', {
      method: 'POST',
      body: JSON.stringify(Object.fromEntries(formData)),
    })
    if (!response.ok) throw new Error('Failed')
    return { success: true }
  } catch (error) {
    return { success: false, error: 'Something went wrong' }
  }
}
```

**After:**
```typescript
import { formActionWrapper } from '@/lib/errors'
import { z } from 'zod'

const ItemSchema = z.object({
  name: z.string().min(2),
  description: z.string(),
})

export const createItem = formActionWrapper({
  schema: ItemSchema,
  transformFormData: (fd) => ({
    name: fd.get('name') as string,
    description: fd.get('description') as string,
  }),
  action: async (data) => {
    await api.post('/api/items/', data)
    revalidatePath('/items')
  },
  errorMessage: 'Failed to create item',
})
// Automatic validation, error handling, and logging
```

### Component Error Handling

**Before:**
```typescript
export default async function Page() {
  const data = await fetchData()
  return <div>{data.name}</div>
}
// Crashes entire page if fetchData fails
```

**After:**
```typescript
import { ErrorBoundary } from '@/components/error/error-boundary'

export default async function Page() {
  return (
    <ErrorBoundary>
      <DataComponent />
    </ErrorBoundary>
  )
}

async function DataComponent() {
  const data = await fetchData()
  return <div>{data.name}</div>
}
// Errors caught and displayed gracefully
```

---

## Error Logging

### Development Mode
- Errors logged to console with full details
- Stack traces displayed
- Context information included

### Production Mode
- Errors logged to monitoring service (Sentry-ready)
- PII excluded from logs
- Error IDs (digest) for tracking
- Context metadata included

**Integration Example:**
```typescript
// src/lib/errors/error-handler.ts

import * as Sentry from '@sentry/nextjs'

export function logError(error: Error, context?: Record<string, any>) {
  if (process.env.NODE_ENV === 'production') {
    Sentry.captureException(error, { extra: context })
  } else {
    console.error('Error logged:', { error, context })
  }
}
```

---

## HTTP Status Code Handling

The API client and error parser handle all common HTTP status codes:

| Code | Message |
|------|---------|
| 400 | Invalid request. Please check your input and try again. |
| 401 | Your session has expired. Please log in again. |
| 403 | You do not have permission to perform this action. |
| 404 | The requested resource was not found. |
| 409 | This action conflicts with existing data. |
| 422 | The data provided is invalid. |
| 429 | Too many requests. Please try again later. |
| 500 | A server error occurred. Please try again later. |
| 503 | The service is temporarily unavailable. |

---

## Retry Logic

Automatic retry with exponential backoff for transient errors:

```typescript
import { retryWithBackoff } from '@/lib/errors'

const data = await retryWithBackoff(
  async () => await api.get('/api/unreliable-endpoint/'),
  3,  // max retries
  1000 // base delay (1 second)
)

// Retry sequence:
// 1st attempt: immediate
// 2nd attempt: after 1 second
// 3rd attempt: after 2 seconds
// 4th attempt: after 4 seconds
```

**Smart Retry:**
- Retries on network errors and 5xx responses
- **Does NOT** retry on:
  - Authentication errors (401)
  - Authorization errors (403)
  - Validation errors (400, 422)

---

## Validation Error Handling

Zod validation errors are automatically formatted:

```typescript
import { formatZodError } from '@/lib/errors'

const validation = schema.safeParse(data)

if (!validation.success) {
  const fields = formatZodError(validation.error)
  // fields = {
  //   email: ['Invalid email format'],
  //   password: ['Password must be at least 8 characters'],
  // }
  return { success: false, error: 'Validation failed', fields }
}
```

---

## Testing Error Handling

### Unit Tests

```typescript
import { parseApiError, ApiError } from '@/lib/errors'

describe('Error Utilities', () => {
  it('should parse 401 errors correctly', () => {
    const error = new ApiError('Unauthorized', 401)
    const message = parseApiError(error)
    expect(message).toContain('session has expired')
  })

  it('should format field errors', () => {
    const zodError = schema.safeParse(invalidData).error
    const fields = formatZodError(zodError)
    expect(fields).toHaveProperty('email')
  })
})
```

### E2E Tests

```typescript
test('should display error message on failed submission', async ({ page }) => {
  await page.goto('/form')
  await page.fill('input[name="email"]', 'invalid')
  await page.click('button[type="submit"]')

  await expect(page.getByRole('alert')).toContainText('Invalid email')
})
```

---

## Build Status

✅ **Build Successful**

```
Route (app)
├ ○ /login
├ ○ /forgot-password
├ ƒ /reset-password
├ ƒ /dashboard
├ ƒ /applications
├ ƒ /candidates
├ ƒ /interviews
├ ƒ /offers
├ ƒ /requisitions
└ ƒ /settings

○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand

✓ All TypeScript checks passed
✓ No build errors
```

---

## Files Created

### Error Utilities
- ✅ [src/lib/errors/error-handler.ts](apps/internal-dashboard/src/lib/errors/error-handler.ts) - Core error utilities
- ✅ [src/lib/errors/api-client.ts](apps/internal-dashboard/src/lib/errors/api-client.ts) - Centralized API client
- ✅ [src/lib/errors/server-action-wrapper.ts](apps/internal-dashboard/src/lib/errors/server-action-wrapper.ts) - Server Action wrappers
- ✅ [src/lib/errors/index.ts](apps/internal-dashboard/src/lib/errors/index.ts) - Public exports

### Error Components
- ✅ [src/components/error/error-boundary.tsx](apps/internal-dashboard/src/components/error/error-boundary.tsx) - React Error Boundary
- ✅ [src/components/error/error-message.tsx](apps/internal-dashboard/src/components/error/error-message.tsx) - Error message components

### Error Pages
- ✅ [src/app/error.tsx](apps/internal-dashboard/src/app/error.tsx) - Root error page (updated)
- ✅ [src/app/global-error.tsx](apps/internal-dashboard/src/app/global-error.tsx) - Global error page (updated)
- ✅ [src/app/not-found.tsx](apps/internal-dashboard/src/app/not-found.tsx) - 404 page (created)

---

## Migration Guide

### Migrating Existing Code

**Step 1: Replace fetch calls with API client**
```typescript
// Old
const response = await fetch(`${API_URL}/api/v1/users/`, {
  headers: await getAuthHeaders(),
})
const users = await response.json()

// New
import { api } from '@/lib/errors'
const users = await api.get('/api/v1/users/')
```

**Step 2: Wrap Server Actions**
```typescript
// Old
export async function createUser(formData: FormData) {
  try {
    // ... implementation
    return { success: true }
  } catch (error) {
    return { success: false, error: 'Failed' }
  }
}

// New
import { formActionWrapper } from '@/lib/errors'
export const createUser = formActionWrapper({
  schema: UserSchema,
  action: async (data) => {
    // ... implementation
  },
})
```

**Step 3: Add Error Boundaries**
```typescript
// Wrap page sections that might error
<ErrorBoundary>
  <ComponentThatMightFail />
</ErrorBoundary>
```

---

## Best Practices

### 1. Always Use the API Client
```typescript
// ✅ Good
import { api } from '@/lib/errors'
const data = await api.get('/endpoint')

// ❌ Avoid
const response = await fetch('/endpoint')
```

### 2. Wrap Server Actions
```typescript
// ✅ Good
export const myAction = actionWrapper({ ... })

// ❌ Avoid
export async function myAction() {
  try { ... } catch { ... }
}
```

### 3. Use Error Boundaries for UI
```typescript
// ✅ Good
<ErrorBoundary>
  <FeatureComponent />
</ErrorBoundary>

// ❌ Avoid
// No error boundary, entire page crashes
```

### 4. Display User-Friendly Errors
```typescript
// ✅ Good
<ErrorMessage message={parseApiError(error)} />

// ❌ Avoid
<p>{error.message}</p> // May expose technical details
```

### 5. Log Errors with Context
```typescript
// ✅ Good
logError(error, { userId, action: 'create-offer' })

// ❌ Avoid
console.error(error) // No context for debugging
```

---

## Future Enhancements

### High Priority
- [ ] Integrate Sentry for production error tracking
- [ ] Add error rate monitoring and alerting
- [ ] Create error analytics dashboard
- [ ] Add offline error queue

### Medium Priority
- [ ] Add retry UI for failed actions
- [ ] Implement optimistic UI with rollback
- [ ] Add error recovery suggestions
- [ ] Create error pattern library

### Low Priority
- [ ] Add A/B testing for error messages
- [ ] Implement smart error aggregation
- [ ] Add user feedback on errors
- [ ] Create error reproduction tool

---

## Summary

✅ **Error Handling System Complete**

**Implemented:**
- Centralized error utilities with custom error classes
- API client with automatic error handling and logging
- Server Action wrappers with validation
- React Error Boundary component
- Error message components (ErrorMessage, FieldError)
- Enhanced error pages (error, global-error, not-found)
- Automatic error logging (Sentry-ready)
- Retry logic with exponential backoff
- HTTP status code handling
- Zod validation error formatting

**Benefits:**
- Consistent error handling across application
- User-friendly error messages
- Automatic error logging and monitoring
- Reduced boilerplate code
- Type-safe error handling
- Better debugging experience
- Improved user experience

**All builds passing, production-ready!**

---

**Last Updated:** February 16, 2026
**Status:** Complete and Production-Ready ✅
