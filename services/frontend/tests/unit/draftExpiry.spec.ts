import { describe, expect, it } from 'vitest'
import { draftRemainingMs } from '~/utils/draftExpiry'

const SERVER_NOW = 1_700_000_000 // unix seconds

describe('draftRemainingMs', () => {
  it('is null for a draft that never expires', () => {
    expect(draftRemainingMs({ expires_at: null, server_time: SERVER_NOW }, 0, 0)).toBeNull()
  })

  it('starts at the server-side window when just received', () => {
    const draft = { expires_at: SERVER_NOW + 600, server_time: SERVER_NOW }
    expect(draftRemainingMs(draft, 5_000, 5_000)).toBe(600_000)
  })

  it('counts down with time elapsed in the browser', () => {
    const draft = { expires_at: SERVER_NOW + 600, server_time: SERVER_NOW }
    expect(draftRemainingMs(draft, 5_000, 5_000 + 90_000)).toBe(510_000)
  })

  it('ignores how far the browser clock is from the server clock', () => {
    const draft = { expires_at: SERVER_NOW + 120, server_time: SERVER_NOW }
    const skewedBrowserNow = SERVER_NOW * 1000 + 3_600_000 // an hour ahead
    expect(draftRemainingMs(draft, skewedBrowserNow, skewedBrowserNow)).toBe(120_000)
  })

  it('goes negative once the window has passed', () => {
    const draft = { expires_at: SERVER_NOW + 10, server_time: SERVER_NOW }
    expect(draftRemainingMs(draft, 0, 11_000)).toBeLessThan(0)
  })
})
