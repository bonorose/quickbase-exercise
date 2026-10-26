import { expect, test } from '@playwright/test'

test.describe('pending revisions', { tag: '@mocks' }, () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test('an operator drafts a change and approves it from the review panel', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Email').fill('op1@excellence.qai.local')
    await page.getByLabel('Password').fill('admin123')
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.getByRole('link', { name: 'Tickets' }).click()
    const ticket = page.getByRole('row', { name: /^1 Excellence ticket 1\b/ })
    await expect(ticket).toBeVisible()
    await ticket.click()
    await expect(page).toHaveURL(/id=1/)
    const workedOn = page.getByTestId('open-draft')
    const startWorking = page.getByTestId('start-working')
    await expect(workedOn.or(startWorking)).toBeVisible()
    if (await workedOn.isVisible()) {
      await expect(workedOn).toContainText('Being worked on by')
    }
    else {
      await startWorking.click()
      await expect(page).toHaveURL(/\/drafts\?id=/, { timeout: 10_000 })
      await page.getByTestId('draft-priority').selectOption('high')
      await page.getByTestId('draft-save').click()
      await page.getByTestId('draft-approve').click()
      await expect(page.getByTestId('draft-editor')).toHaveCount(0)
    }

    await page.getByRole('link', { name: 'Audit' }).click()
    await expect(page.getByRole('heading', { name: 'Audit' })).toBeVisible()
    await expect(page.getByText('login')).toBeVisible()
    await expect(page.getByText('pending_revision_approved')).toBeVisible()
    await expect(page.getByText('ticket_mutated')).toBeVisible()

    await page.goto('/review')
    await expect(page.getByTestId('not-found-state')).toBeVisible()
    await expect(page.getByTestId('not-found-state')).not.toContainText(/permission/i)
  })

  test('a team lead approves a tainted draft the operator cannot', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Email').fill('lead@excellence.qai.local')
    await page.getByLabel('Password').fill('admin123')
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.getByRole('link', { name: 'Review' }).click()
    await expect(page.getByRole('heading', { name: 'Review' })).toBeVisible()
    await page.getByRole('button', { name: /Needs a team lead|by Excellence/ }).first().click()
    await expect(page.getByText('A team lead has to approve it.')).toBeVisible()
    await page.getByTestId('draft-approve').click()
    await expect(page.getByText('Nothing is waiting for review')).toBeVisible()
    await page.getByRole('link', { name: 'Audit' }).click()
    await expect(page.getByTestId('audit-ticket-filter')).toBeVisible()
    await expect(page.getByText('pending_revision_approved')).toBeVisible()
  })
})
