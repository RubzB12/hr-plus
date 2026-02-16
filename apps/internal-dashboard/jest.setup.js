// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom'
import fetchMock from 'jest-fetch-mock'

// Enable fetch mocks
fetchMock.enableMocks()

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      pathname: '/',
      query: {},
      asPath: '/',
    }
  },
  usePathname() {
    return '/'
  },
  useSearchParams() {
    return new URLSearchParams()
  },
  redirect: jest.fn(),
}))

// Mock Next.js cookies
jest.mock('next/headers', () => ({
  cookies: jest.fn(() => ({
    get: jest.fn(),
    set: jest.fn(),
    delete: jest.fn(),
    getAll: jest.fn(() => []),
  })),
  headers: jest.fn(() => ({
    get: jest.fn(),
  })),
}))

// Reset mocks before each test
beforeEach(() => {
  fetchMock.resetMocks()
  jest.clearAllMocks()
})
