/**
 * Threat: a second click or a smuggled field executes a different mutation.
 * Control: extra body fields are 422; a second C-10 is 409; foreign ids are 404.
 */
import { expect, test } from '@playwright/test'
import { E2E_PASSWORD, loginThroughUi, QUANTUM_EMAIL } from '../fixtures/auth'
import { api, claimableTicketId, firstTicketId, ticketState } from '../helpers'

test.describe('adversarial decision integrity', { tag: ['@adversarial'] }, () => {
  test.describe.configure({ mode: 'serial' })
  test.use({ storageState: { cookies: [], origins: [] } })

  test.beforeEach(async ({ page }) => {
    await loginThroughUi(page, 'op1@excellence.qai.local', E2E_PASSWORD)
  })
  test('a tampered approve is rejected and a second approve conflicts', async ({ page }) => {
    const ticketId = await claimableTicketId(page)
    const before = await ticketState(page, ticketId)
    const claimed = await api(page, 'POST', `/api/v1/tickets/${ticketId}/pending-revisions`, {
      action: 'update',
      changed_contents: { priority: 'high' },
    })
    expect(claimed.status()).toBe(201)
    const draftId = (await claimed.json()).id as string

    const smuggled = await api(page, 'POST', `/api/v1/pending-revisions/${draftId}/approve`, {
      changed_contents: { description: 'stolen' },
      organization_id: 2,
    })
    expect(smuggled.status()).toBe(422)

    const approved = await api(page, 'POST', `/api/v1/pending-revisions/${draftId}/approve`, {})
    expect(approved.status()).toBe(200)
    const again = await api(page, 'POST', `/api/v1/pending-revisions/${draftId}/approve`, {})
    expect(again.status()).toBe(409)
    const after = await ticketState(page, ticketId)
    expect(after.priority).toBe('high')
    expect(after.contents).toBe(before.contents)
    expect(after.title).toBe(before.title)
  })

  test('approving another organization\'s draft is 404', async ({ page, browser }) => {
    const quantum = await browser.newContext({ storageState: { cookies: [], origins: [] } })
    const quantumPage = await quantum.newPage()
    await loginThroughUi(quantumPage, QUANTUM_EMAIL, E2E_PASSWORD)
    const foreignId = await firstTicketId(quantumPage)
    const claimed = await api(quantumPage, 'POST', `/api/v1/tickets/${foreignId}/pending-revisions`, {
      action: 'update',
      changed_contents: { priority: 'low' },
    })
    expect(claimed.status()).toBe(201)
    const draftId = (await claimed.json()).id as string
    await quantum.close()

    const denied = await api(page, 'POST', `/api/v1/pending-revisions/${draftId}/approve`, {})
    expect(denied.status()).toBe(404)
  })

  test('double submit creates one revision', async ({ page }) => {
    await loginThroughUi(page, 'op2@excellence.qai.local')
    const ticketId = await claimableTicketId(page)
    const claimed = await api(page, 'POST', `/api/v1/tickets/${ticketId}/pending-revisions`, {
      action: 'update',
      changed_contents: { priority: 'medium' },
    })
    expect(claimed.status()).toBe(201)
    const draftId = (await claimed.json()).id as string
    const [first, second] = await Promise.all([
      api(page, 'POST', `/api/v1/pending-revisions/${draftId}/approve`, {}),
      api(page, 'POST', `/api/v1/pending-revisions/${draftId}/approve`, {}),
    ])
    const statuses = [first.status(), second.status()].sort()
    expect(statuses).toEqual([200, 409])
    const after = await ticketState(page, ticketId)
    expect(after.priority).toBe('medium')
  })
})
