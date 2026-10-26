import { describe, expect, it } from 'vitest'
import { ApiError, parseRetryAfter } from '~/api/client'
import { getApiErrorMessage, isNotFound, retryAfterSeconds, safeRedirectPath } from '~/utils/apiError'

describe('getApiErrorMessage', () => {
  it('returns the network fallback when there is no status', () => {
    expect(getApiErrorMessage({}, 'fallback')).toBe('Can\'t reach qAI. Check your connection or try again')
  })

  it('reads a string detail', () => {
    expect(getApiErrorMessage({ status: 401, data: { detail: 'Nope' } }, 'fallback')).toBe('Nope')
  })

  it('reads the first FastAPI validation message', () => {
    expect(getApiErrorMessage({
      status: 422,
      data: { detail: [{ msg: 'Field required', loc: ['body', 'email'] }] },
    }, 'fallback')).toBe('Field required')
  })

  it('uses the fallback when detail is missing', () => {
    expect(getApiErrorMessage({ status: 500, data: {} }, 'fallback')).toBe('fallback')
  })
})

describe('safeRedirectPath', () => {
  it('keeps same-app paths', () => {
    expect(safeRedirectPath('/tickets?id=1')).toBe('/tickets?id=1')
  })

  it('rejects protocol-relative URLs', () => {
    expect(safeRedirectPath('//evil.com')).toBe('/')
  })

  it('rejects non-strings', () => {
    expect(safeRedirectPath(['/x'])).toBe('/')
  })
})

describe('parseRetryAfter', () => {
  it('reads seconds and HTTP dates', () => {
    expect(parseRetryAfter('12')).toBe(12)
    const later = new Date(Date.now() + 15_000).toUTCString()
    const parsed = parseRetryAfter(later)
    expect(parsed).toBeGreaterThanOrEqual(14)
    expect(parsed).toBeLessThanOrEqual(16)
  })
})

describe('retryAfterSeconds', () => {
  it('falls back to 30 when the 429 has no header', () => {
    expect(retryAfterSeconds(new ApiError(429, { detail: 'slow down' }))).toBe(30)
  })

  it('uses the parsed header on ApiError', () => {
    expect(retryAfterSeconds(new ApiError(429, { detail: 'slow down' }, '8'))).toBe(8)
  })
})

describe('isNotFound', () => {
  it('detects ApiError 404', () => {
    expect(isNotFound(new ApiError(404, { detail: 'gone' }))).toBe(true)
  })

  it('detects $fetch-shaped 404', () => {
    expect(isNotFound({ status: 404, data: { detail: 'gone' } })).toBe(true)
  })

  it('is false for other statuses', () => {
    expect(isNotFound({ status: 401 })).toBe(false)
  })
})
