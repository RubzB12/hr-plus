import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Start from the login page
    await page.goto('/login')
  })

  test.describe('Login', () => {
    test('should display login form', async ({ page }) => {
      await expect(page.getByRole('heading', { name: 'HR-Plus' })).toBeVisible()
      await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible()
      await expect(page.getByLabel('Email')).toBeVisible()
      await expect(page.getByLabel('Password')).toBeVisible()
      await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible()
    })

    test('should show validation errors for empty fields', async ({ page }) => {
      await page.getByRole('button', { name: 'Sign in' }).click()

      // HTML5 validation should prevent submission
      const emailInput = page.getByLabel('Email')
      await expect(emailInput).toHaveAttribute('required')

      const passwordInput = page.getByLabel('Password')
      await expect(passwordInput).toHaveAttribute('required')
    })

    test('should show error for invalid credentials', async ({ page }) => {
      await page.getByLabel('Email').fill('wrong@example.com')
      await page.getByLabel('Password').fill('wrongpassword')
      await page.getByRole('button', { name: 'Sign in' }).click()

      // Wait for error message
      await expect(page.getByText(/invalid email or password/i)).toBeVisible()
    })

    test('should redirect to dashboard on successful login', async ({ page }) => {
      // Mock successful login - in real tests, use test credentials
      await page.route('**/api/v1/auth/login/', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: '123',
            email: 'test@example.com',
            first_name: 'Test',
            last_name: 'User',
          }),
          headers: {
            'set-cookie': 'sessionid=test-session-token; Path=/; HttpOnly',
          },
        })
      })

      await page.getByLabel('Email').fill('test@example.com')
      await page.getByLabel('Password').fill('password123')
      await page.getByRole('button', { name: 'Sign in' }).click()

      // Should redirect to dashboard
      await expect(page).toHaveURL('/dashboard')
    })

    test('should show forgot password link', async ({ page }) => {
      const forgotLink = page.getByRole('link', { name: /forgot password/i })
      await expect(forgotLink).toBeVisible()
      await forgotLink.click()

      await expect(page).toHaveURL('/forgot-password')
    })
  })

  test.describe('Logout', () => {
    test.beforeEach(async ({ page, context }) => {
      // Set session cookie to simulate logged-in state
      await context.addCookies([
        {
          name: 'session',
          value: 'test-session-token',
          domain: 'localhost',
          path: '/',
          httpOnly: true,
          secure: false,
          sameSite: 'Lax',
        },
      ])

      // Mock the /api/v1/auth/me/ endpoint
      await page.route('**/api/v1/auth/me/', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: '123',
            email: 'test@example.com',
            first_name: 'Test',
            last_name: 'User',
            is_internal: true,
            internal_profile: {
              title: 'Recruiter',
            },
          }),
        })
      })

      await page.goto('/dashboard')
    })

    test('should show user menu when logged in', async ({ page }) => {
      // Click on avatar to open dropdown
      const avatar = page.getByRole('button', { name: /TU/i })
      await expect(avatar).toBeVisible()
      await avatar.click()

      // Check for user info in dropdown
      await expect(page.getByText('Test User')).toBeVisible()
      await expect(page.getByText('test@example.com')).toBeVisible()
    })

    test('should logout successfully', async ({ page }) => {
      // Mock logout endpoint
      await page.route('**/api/v1/auth/logout/', async (route) => {
        await route.fulfill({
          status: 204,
        })
      })

      // Open user menu
      const avatar = page.getByRole('button', { name: /TU/i })
      await avatar.click()

      // Click sign out
      await page.getByRole('button', { name: /sign out/i }).click()

      // Should redirect to login
      await expect(page).toHaveURL('/login')
    })
  })

  test.describe('Password Reset', () => {
    test('should display forgot password form', async ({ page }) => {
      await page.goto('/forgot-password')

      await expect(page.getByRole('heading', { name: 'Reset Password' })).toBeVisible()
      await expect(page.getByLabel('Email')).toBeVisible()
      await expect(page.getByRole('button', { name: /send reset link/i })).toBeVisible()
      await expect(page.getByRole('link', { name: /back to login/i })).toBeVisible()
    })

    test('should show success message on password reset request', async ({ page }) => {
      await page.goto('/forgot-password')

      // Mock API endpoint
      await page.route('**/api/v1/auth/password-reset/', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'If the email exists, a reset link has been sent.',
          }),
        })
      })

      await page.getByLabel('Email').fill('test@example.com')
      await page.getByRole('button', { name: /send reset link/i }).click()

      await expect(page.getByText(/if an account exists/i)).toBeVisible()
    })

    test('should allow password reset with valid token', async ({ page }) => {
      await page.goto('/reset-password?token=valid-reset-token')

      await expect(page.getByRole('heading', { name: 'Set New Password' })).toBeVisible()
      await expect(page.getByLabel('New Password')).toBeVisible()
      await expect(page.getByLabel('Confirm Password')).toBeVisible()
    })

    test('should show error for invalid reset link', async ({ page }) => {
      await page.goto('/reset-password')

      await expect(page.getByRole('heading', { name: 'Invalid Link' })).toBeVisible()
    })

    test('should validate password confirmation match', async ({ page }) => {
      await page.goto('/reset-password?token=valid-token')

      // Mock API endpoint
      await page.route('**/api/v1/auth/password-reset/confirm/', async (route) => {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: "Passwords don't match",
          }),
        })
      })

      await page.getByLabel('New Password').fill('newpassword123')
      await page.getByLabel('Confirm Password').fill('differentpassword')
      await page.getByRole('button', { name: /reset password/i }).click()

      await expect(page.getByText(/passwords don't match/i)).toBeVisible()
    })
  })

  test.describe('Protected Routes', () => {
    test('should redirect unauthenticated user to login', async ({ page }) => {
      await page.goto('/dashboard')

      // Should be redirected to login
      await expect(page).toHaveURL('/login')
    })

    test('should allow access to dashboard when authenticated', async ({ page, context }) => {
      // Set session cookie
      await context.addCookies([
        {
          name: 'session',
          value: 'test-session-token',
          domain: 'localhost',
          path: '/',
          httpOnly: true,
        },
      ])

      await page.goto('/dashboard')

      // Should stay on dashboard
      await expect(page).toHaveURL('/dashboard')
    })

    test('should redirect authenticated user away from login page', async ({ page, context }) => {
      // Set session cookie
      await context.addCookies([
        {
          name: 'session',
          value: 'test-session-token',
          domain: 'localhost',
          path: '/',
          httpOnly: true,
        },
      ])

      await page.goto('/login')

      // Should be redirected to dashboard
      await expect(page).toHaveURL('/dashboard')
    })
  })
})
