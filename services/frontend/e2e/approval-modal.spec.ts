/**
 * Requirement: "an approval modal that blocks execution until clicked".
 * The fake provider's scripts draft changes on ticket #1, so this needs LLM_PROVIDER=fake.
 * Control: the modal opens after the turn, can't be dismissed by Escape or the backdrop,
 * and only Approve writes the ticket. A tainted draft offers no Approve to an operator.
 */
import { expect, test, type Page } from '@playwright/test'
import { E2E_PASSWORD, loginThroughUi } from './fixtures/auth'
import { api, ticketState } from './helpers'

const TICKET = '1'
const requireFake = (process.env.LLM_PROVIDER ?? process.env.E2E_LLM_PROVIDER) === 'fake'

function missing(message: string): never {
  if (requireFake) throw new Error(message)
  test.skip(true, message)
  throw new Error(message)
}

/** Earlier specs draft on the same ticket. Start each test without an open draft. */
async function clearOpenDraft(page: Page) {
  const state = await ticketState(page, TICKET)
  if (state.open_pending_revision) {
    await api(page, 'POST', `/api/v1/pending-revisions/${state.open_pending_revision.id}/reject`, {})
  }
}

async function sendTurn(page: Page, text: string) {
  await page.goto('/chat')
  await expect(page.getByRole('heading', { name: 'Chat', exact: true })).toBeVisible({ timeout: 20_000 })
  await page.getByTestId('chat-composer').fill(text)
  await page.getByTestId('chat-send').click()
  const modal = page.getByRole('alertdialog')
  try {
    await expect(modal).toBeVisible({ timeout: 20_000 })
  }
  catch {
    missing('No draft was proposed — run the backend with LLM_PROVIDER=fake')
  }
  return modal
}

async function expectStillBlocking(page: Page) {
  const modal = page.getByRole('alertdialog')
  await page.keyboard.press('Escape')
  await expect(modal).toBeVisible()
  // The overlay covers the whole viewport; click its bottom-left corner, away from the dialog.
  const viewport = page.viewportSize() ?? { width: 1280, height: 720 }
  await page.mouse.click(10, viewport.height - 10)
  await expect(modal).toBeVisible()
}

test.describe('chat approval modal', { tag: ['@chat', '@gate'] }, () => {
  test.describe.configure({ mode: 'serial' })
  test.use({ storageState: { cookies: [], origins: [] } })

  test.beforeEach(async ({ page }) => {
    await loginThroughUi(page, 'op1@excellence.qai.local', E2E_PASSWORD)
    await clearOpenDraft(page)
  })

  test('opens after the turn, blocks until clicked, and only Approve writes the ticket', async ({ page }) => {
    const before = await ticketState(page, TICKET)
    const modal = await sendTurn(page, 'close the billing ticket')

    // Opens once the turn has finished: the assistant's closing text is already there.
    await expect(page.getByText('It will not apply until you approve it.')).toBeVisible()
    await expect(modal.getByRole('heading', { name: 'Approve this change?' })).toBeVisible()
    await expect(modal).toContainText(`ticket #${TICKET}`)
    await expect(modal.getByTestId('draft-approve')).toBeVisible()

    await expectStillBlocking(page)
    expect((await ticketState(page, TICKET)).priority).toBe(before.priority)

    // "Decide later" closes the modal without deciding; the draft stays open.
    await modal.getByTestId('approval-later').click()
    await expect(modal).toBeHidden()
    await expect(page.getByTestId('approval-waiting')).toContainText('waiting for your decision')
    await expect(page.getByTestId('tool-trace')).toContainText('Awaiting approval')
    const waiting = await ticketState(page, TICKET)
    expect(waiting.priority).toBe(before.priority)
    expect(waiting.open_pending_revision).not.toBeNull()

    await page.getByTestId('approval-reopen').click()
    await expect(modal).toBeVisible()
    await modal.getByTestId('draft-approve').click()
    await expect(modal).toBeHidden()

    const after = await ticketState(page, TICKET)
    expect(after.priority).toBe('high')
    expect(after.open_pending_revision).toBeNull()
    await expect(page.getByTestId('tool-trace')).toContainText('Approved')
    await expect(page.getByTestId('approval-waiting')).toHaveCount(0)
  })

  test('a tainted draft offers an operator no Approve and stays unexecuted', async ({ page }) => {
    const before = await ticketState(page, TICKET)
    const modal = await sendTurn(page, 'draft a tainted billing change')

    await expect(modal).toContainText('A team lead has to approve it.')
    await expect(modal.getByTestId('draft-approve')).toHaveCount(0)
    await expect(modal.getByTestId('approval-later')).toHaveText('Leave for team lead')
    await expectStillBlocking(page)

    await modal.getByTestId('approval-later').click()
    await expect(modal).toBeHidden()
    await expect(page.getByTestId('approval-waiting')).toContainText('waiting for a team lead')

    // The server enforces the same rule the UI shows.
    const draft = await ticketState(page, TICKET)
    expect(draft.open_pending_revision).not.toBeNull()
    const denied = await api(page, 'POST', `/api/v1/pending-revisions/${draft.open_pending_revision!.id}/approve`, {})
    expect(denied.status()).toBe(403)

    const after = await ticketState(page, TICKET)
    expect(after.priority).toBe(before.priority)
    await clearOpenDraft(page)
  })
})
