/**
 * Threat: dismissing or reloading the review UI executes a mutation.
 * Control: close ≠ approve (D-21). C-08 stays open. Only C-10 writes the ticket.
 */
import { expect, test } from '@playwright/test'
import { E2E_PASSWORD, loginThroughUi } from '../fixtures/auth'
import { api, firstTicketId, ticketState } from '../helpers'

test.describe('adversarial approval bypass', { tag: ['@adversarial'] }, () => {
  test.describe.configure({ mode: 'serial' })
  test.use({ storageState: { cookies: [], origins: [] } })

  test.beforeEach(async ({ page }) => {
    await loginThroughUi(page, 'op1@excellence.qai.local', E2E_PASSWORD)
  })
  test('closing the review sheet does not change the ticket', async ({ page }) => {
    const ticketId = await firstTicketId(page)
    const before = await ticketState(page, ticketId)
    await page.goto(`/tickets?id=${ticketId}`)
    const openDraft = page.getByRole('link', { name: 'Open draft' })
    if (await openDraft.isVisible().catch(() => false)) {
      await openDraft.click()
      await expect(page.getByTestId('draft-editor')).toBeVisible()
      await page.getByRole('button', { name: 'Close' }).click()
      await expect(page.getByTestId('draft-editor')).toHaveCount(0)
    }
    await page.keyboard.press('Escape')
    await page.reload()
    const after = await ticketState(page, ticketId)
    expect(after.status).toBe(before.status)
    expect(after.priority).toBe(before.priority)
    expect(after.contents).toBe(before.contents)
  })

  test('reload keeps a pending agent draft and does not write the ticket', async ({ page }) => {
    await page.goto('/chat')
    await page.getByTestId('chat-composer').fill('close the billing ticket')
    await page.getByTestId('chat-send').click()
    await expect(page.getByText('Awaiting approval')).toBeVisible({ timeout: 20_000 })
    await expect(page.getByTestId('chat-composer')).toBeEnabled()
    // The draft lives in this conversation; /chat alone is a new, empty one.
    await expect(page).toHaveURL(/\/chat\/[0-9a-f-]{36}/i)
    const chatUrl = page.url()

    await page.goto('/drafts')
    const row = page.locator('[data-testid^="draft-row-"]').first()
    await expect(row).toBeVisible()
    const ticketId = await row.getAttribute('data-ticket-id')
    const draftId = await row.getAttribute('data-draft-id')
    expect(ticketId).toBeTruthy()
    expect(draftId).toBeTruthy()

    try {
      const before = await ticketState(page, ticketId!)

      await page.reload()
      await expect(page.getByTestId(`draft-row-${ticketId}`)).toBeVisible()

      // Back in the conversation, a reload brings the draft back for review, still unexecuted.
      await page.goto(chatUrl)
      await page.reload()
      await expect(page.getByText('Awaiting approval')).toBeVisible({ timeout: 20_000 })
      await expect(page.getByRole('alertdialog')).toBeVisible()

      const after = await ticketState(page, ticketId!)
      expect(after.priority).toBe(before.priority)
      expect(after.contents).toBe(before.contents)
      expect(after.open_pending_revision?.id).toBe(draftId)
    }
    finally {
      // Leave ticket #1 without an open draft, or later specs merge into this one.
      await api(page, 'POST', `/api/v1/pending-revisions/${draftId}/reject`, {})
    }
  })

  test('an operator cannot approve a tainted draft', async ({ page }) => {
    await page.goto('/chat')
    await page.getByTestId('chat-composer').fill('draft a tainted billing change')
    await page.getByTestId('chat-send').click()
    await expect(page.getByText('A team lead has to approve this draft.')).toBeVisible({ timeout: 20_000 })

    await page.goto('/drafts')
    const row = page.locator('[data-testid^="draft-row-"]').first()
    await expect(row).toBeVisible()
    const ticketId = await row.getAttribute('data-ticket-id')
    const draftId = await row.getAttribute('data-draft-id')
    expect(ticketId).toBeTruthy()
    expect(draftId).toBeTruthy()

    try {
      const before = await ticketState(page, ticketId!)
      await row.click()
      await expect(page.getByRole('dialog').getByText('A team lead has to approve it.')).toBeVisible()
      await expect(page.getByTestId('draft-approve')).toHaveCount(0)
      const denied = await api(page, 'POST', `/api/v1/pending-revisions/${draftId}/approve`, {})
      expect(denied.status()).toBe(403)
      const after = await ticketState(page, ticketId!)
      expect(after.priority).toBe(before.priority)
      expect(after.contents).toBe(before.contents)
    }
    finally {
      // A leftover tainted draft on ticket #1 would absorb later specs' changes and hide their Approve.
      await api(page, 'POST', `/api/v1/pending-revisions/${draftId}/reject`, {})
    }
  })
})
