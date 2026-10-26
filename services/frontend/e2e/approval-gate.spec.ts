import { expect, test, type Page } from '@playwright/test'
import { E2E_PASSWORD, loginThroughUi } from './fixtures/auth'

test.describe('approval gate', { tag: '@gate' }, () => {
  test.describe.configure({ mode: 'serial' })
  test.use({ storageState: { cookies: [], origins: [] } })
  test.setTimeout(120_000)

  async function firstDraftRow(page: Page) {
    const row = page.locator('[data-testid^="draft-row-"]').first()
    await expect(row).toBeVisible({ timeout: 20_000 })
    const ticketId = await row.getAttribute('data-ticket-id')
    if (!ticketId) throw new Error('Draft row is missing data-ticket-id')
    return { row, ticketId }
  }

  async function ticketDrawer(page: Page, ticketId: string) {
    await page.goto(`/tickets?id=${ticketId}`)
    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
    return dialog
  }

  async function openClaimableTicket(page: Page, opts?: { requireNoRevisions?: boolean }) {
    await page.goto('/tickets')
    await expect(page.getByRole('heading', { name: 'Tickets' })).toBeVisible()
    const rows = page.locator('table tbody tr')
    await expect(rows.first()).toBeVisible()
    const ticketIds: string[] = []
    const count = await rows.count()
    for (let i = 0; i < count; i++) {
      const id = (await rows.nth(i).locator('td').first().innerText()).trim()
      if (id) ticketIds.push(id)
    }
    for (const ticketId of ticketIds) {
      const dialog = await ticketDrawer(page, ticketId)
      const start = dialog.getByTestId('start-working')
      const open = dialog.getByTestId('open-draft')
      await expect(start.or(open)).toBeVisible()
      if (!(await start.isVisible())) continue
      if (opts?.requireNoRevisions && !(await dialog.getByText('No revisions yet.').isVisible().catch(() => false))) {
        continue
      }
      return { ticketId, dialog }
    }
    throw new Error('No claimable ticket on the first page')
  }

  test('the fake provider drafts a change and only approve writes the ticket', async ({ page }) => {
    await loginThroughUi(page, 'op1@excellence.qai.local', E2E_PASSWORD)

    await page.goto('/chat')
    await expect(page.getByRole('heading', { name: 'Chat', exact: true })).toBeVisible()
    await page.getByTestId('chat-composer').fill('close the billing ticket')
    await page.getByTestId('chat-send').click()
    await expect(page.getByText('Proposed change')).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText('Awaiting approval')).toBeVisible()
    await expect(page.getByText('It will not apply until you approve it.')).toBeVisible()
    await expect(page).toHaveURL(/\/chat\/[0-9a-f-]{36}/i)
    const chatUrl = page.url()

    await page.goto('/drafts')
    const { row, ticketId } = await firstDraftRow(page)
    const title = (await row.locator('.font-medium').innerText()).trim()

    const before = await ticketDrawer(page, ticketId)
    await expect(before.getByTestId('open-draft')).toContainText('Being worked on by')
    await expect(before.getByText('Critical', { exact: true })).toHaveCount(0)

    await page.goto('/drafts')
    await page.getByRole('button', { name: title }).click()
    await page.getByTestId('draft-priority').selectOption('critical')
    await page.getByTestId('draft-save').click()
    await page.getByTestId('draft-approve').click()
    await expect(page.getByTestId('draft-editor')).toHaveCount(0)

    const after = await ticketDrawer(page, ticketId)
    await expect(after.getByText('Critical', { exact: true })).toBeVisible()
    await expect(after.getByText(/Priority: .+ → critical/).first()).toBeVisible()
    await expect(after.getByTestId('open-draft')).toHaveCount(0)

    await page.goto('/audit')
    await expect(page.getByRole('cell', { name: 'login' }).first()).toBeVisible()
    await expect(page.getByRole('cell', { name: 'pending_revision_approved' }).first()).toBeVisible()
    await expect(page.getByRole('cell', { name: 'ticket_mutated' }).first()).toBeVisible()
    await expect(page.getByRole('cell', { name: 'tool_called' }).first()).toBeVisible()

    await page.goto(chatUrl)
    await expect(page.getByText(/Pending revision .+ was executed by/)).toBeVisible()
    await page.getByTestId('view-audit').click()
    await expect(page).toHaveURL(/\/audit\?session_id=/)
    const toolCalled = page.getByRole('button', { name: 'tool_called' }).first()
    await expect(toolCalled).toBeVisible()
    await toolCalled.click()
    await expect(page.getByText('mutate_ticket')).toBeVisible()

    await page.goto('/chat')
    await page.getByTestId('chat-composer').fill('draft a tainted billing change')
    await page.getByTestId('chat-send').click()
    await expect(page.getByText('A team lead has to approve this draft.')).toBeVisible({ timeout: 20_000 })

    await page.goto('/drafts')
    const tainted = await firstDraftRow(page)
    await tainted.row.click()
    await expect(page.getByText('A team lead has to approve it.')).toBeVisible()
    await expect(page.getByTestId('draft-approve')).toHaveCount(0)

    await page.goto('/review')
    await expect(page.getByTestId('not-found-state')).toBeVisible()
    await expect(page.getByTestId('not-found-state')).not.toContainText(/permission/i)

    await page.getByRole('button', { name: 'Sign out' }).click()
    await loginThroughUi(page, 'lead@excellence.qai.local', E2E_PASSWORD)
    await page.getByRole('link', { name: 'Review' }).click()
    await page.locator('[data-testid^="review-row-"]').first().click()
    await expect(page.getByText('A team lead has to approve it.')).toBeVisible()
    await page.getByTestId('draft-approve').click()
    await expect(page.getByText('Nothing is waiting for review.')).toBeVisible()

    await page.goto('/audit')
    await expect(page.getByTestId('audit-ticket-filter')).toBeVisible()
    await page.getByTestId('audit-ticket-filter').fill(tainted.ticketId)
    await page.getByRole('button', { name: 'Filter' }).click()
    await expect(page.getByRole('cell', { name: 'pending_revision_approved' }).first()).toBeVisible()
    await expect(page.getByRole('cell', { name: 'ticket_mutated' }).first()).toBeVisible()

    const leadDrawer = await ticketDrawer(page, tainted.ticketId)
    await expect(leadDrawer.getByText(/Priority: .+ → /).first()).toBeVisible()
    await expect(leadDrawer.getByText('No revisions yet.')).toHaveCount(0)
  })

  test('reject leaves the ticket unchanged', async ({ page }) => {
    await loginThroughUi(page, 'op1@excellence.qai.local', E2E_PASSWORD)
    const { ticketId, dialog } = await openClaimableTicket(page, { requireNoRevisions: true })
    await dialog.getByTestId('start-working').click()
    await expect(page).toHaveURL(/\/drafts\?id=/)
    await page.getByTestId('draft-reject').click()
    await expect(page.getByTestId('draft-editor')).toHaveCount(0)

    const drawer = await ticketDrawer(page, ticketId)
    await expect(drawer.getByText('No revisions yet.')).toBeVisible()
    await expect(drawer.getByTestId('open-draft')).toHaveCount(0)
  })

  test('a colleague claim is 409 with the owner name', async ({ page }) => {
    await loginThroughUi(page, 'op1@excellence.qai.local', E2E_PASSWORD)
    const { ticketId, dialog } = await openClaimableTicket(page)
    await dialog.getByTestId('start-working').click()
    await expect(page).toHaveURL(/\/drafts\?id=/)

    await page.goto('/')
    await page.getByRole('button', { name: /sign out/i }).click()
    await loginThroughUi(page, 'op2@excellence.qai.local', E2E_PASSWORD)
    const colleague = await ticketDrawer(page, ticketId)
    await expect(colleague.getByTestId('open-draft')).toContainText('Being worked on by Martin Georgiev')
    if (await colleague.getByTestId('start-working').isVisible().catch(() => false)) {
      await colleague.getByTestId('start-working').click()
      await expect(page.getByText('Being worked on by Martin Georgiev')).toBeVisible()
    }
  })
})
