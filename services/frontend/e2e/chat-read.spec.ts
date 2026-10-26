import { expect, test } from '@playwright/test'
import { E2E_PASSWORD, E2E_USER_EMAIL, loginThroughUi } from './fixtures/auth'

const requireFake = (process.env.LLM_PROVIDER ?? process.env.E2E_LLM_PROVIDER) === 'fake'

function missing(message: string): never {
  if (requireFake) throw new Error(message)
  test.skip(true, message)
  throw new Error(message)
}

test.describe('chat read path', { tag: ['@chat'] }, () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test.beforeEach(async ({ page }) => {
    await loginThroughUi(page, E2E_USER_EMAIL, E2E_PASSWORD)
  })

  test('streams a billing search and keeps it after reload', async ({ page }) => {
    await page.goto('/chat')
    await expect(page.getByRole('heading', { name: 'Chat', exact: true })).toBeVisible({ timeout: 20_000 })

    const composer = page.getByTestId('chat-composer')
    if (!(await composer.isVisible().catch(() => false))) {
      missing('Chat composer is not available — set LLM_PROVIDER=fake')
    }

    await composer.fill('What\'s blocked on billing?')
    await page.getByTestId('chat-send').click()

    const trace = page.getByTestId('tool-trace')
    try {
      await expect(trace).toBeVisible({ timeout: 20_000 })
    }
    catch {
      missing('Backend did not stream search_tickets — set LLM_PROVIDER=fake')
    }
    await expect(trace).toContainText('Searched tickets')
    await expect(page).toHaveURL(/\/chat\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i, { timeout: 20_000 })

    await trace.getByRole('button').click()
    const ticket = trace.getByRole('link', { name: /billing/i })
    await expect(ticket).toBeVisible()
    await expect(ticket).toHaveAttribute('href', /\/tickets\?id=\d+/)
    await ticket.click()
    await expect(page).toHaveURL(/\/tickets\?id=\d+/)
    await page.goBack()
    await expect(page).toHaveURL(/\/chat\/[0-9a-f-]+/i)

    await page.reload()
    await expect(page.getByTestId('tool-trace')).toContainText('Searched tickets')
  })

  test('stop keeps the partial answer', async ({ page }) => {
    await page.goto('/chat')
    await expect(page.getByRole('heading', { name: 'Chat', exact: true })).toBeVisible({ timeout: 20_000 })
    const composer = page.getByTestId('chat-composer')
    if (!(await composer.isVisible().catch(() => false))) {
      missing('Chat composer is not available — set LLM_PROVIDER=fake')
    }

    await composer.fill('slow answer please')
    await page.getByTestId('chat-send').click()
    await expect(page.getByTestId('chat-stop')).toBeVisible()
    await page.getByTestId('chat-stop').click()
    await expect(page.getByText('Stopped')).toBeVisible()
    await expect(page.getByTestId('chat-send')).toBeVisible()
  })
})
