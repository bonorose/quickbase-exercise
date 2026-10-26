/**
 * Keyboard path (desktop), covered by the keyboard test below:
 * Tab to Email, Password, Sign in. From the dashboard, Tab to Tickets, open a ticket,
 * Tab to Start working, then Tab to Approve.
 * Streaming status is announced once (aria-live=polite). The message list is aria-busy
 * while a turn is in progress and aria-live=off so tokens are not read one by one.
 * A full screen-reader pass (NVDA) is a manual follow-up; this environment has no screen reader.
 */
import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Locator, type Page } from '@playwright/test'
import { E2E_PASSWORD, loginThroughUi } from './fixtures/auth'

test.describe('accessibility', { tag: ['@a11y'] }, () => {
  test.use({ storageState: { cookies: [], origins: [] }, viewport: { width: 1280, height: 800 } })

  test('login, dashboard, tickets, drawer and chat have no serious violations', async ({ page, browser }) => {
    test.setTimeout(90_000)
    const anonymous = await browser.newContext({ storageState: { cookies: [], origins: [] } })
    const login = await anonymous.newPage()
    await login.goto('/login')
    await expect(login.getByRole('heading', { name: 'Sign in' })).toBeVisible()
    await expectClean(login)
    await anonymous.close()

    await loginThroughUi(page, 'op1@excellence.qai.local', E2E_PASSWORD)
    await page.goto('/')
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 20_000 })
    await expectClean(page)

    await page.goto('/tickets')
    await expect(page.getByRole('heading', { name: 'Tickets' })).toBeVisible()
    await expectClean(page)
    const row = page.locator('table tbody tr').first()
    if (await row.isVisible().catch(() => false)) {
      await row.click()
      await expect(page.getByRole('heading', { name: 'AI summary' })).toBeVisible()
      await expectClean(page)
    }

    await page.goto('/chat')
    await expect(page.getByLabel('Message')).toBeVisible()
    await expectClean(page)

    await page.getByTestId('chat-composer').fill('pause please')
    await page.getByTestId('chat-send').click()
    const messages = page.getByTestId('message-list')
    await expect(messages).toHaveAttribute('aria-busy', 'true')
    await expect(page.getByTestId('stream-status')).toHaveAttribute('aria-live', 'polite')
    await expectClean(page)
    await expect(page.getByText('The pause is over.')).toBeVisible({ timeout: 20_000 })
    await expect(messages).toHaveAttribute('aria-busy', 'false')
    await expect(messages).toHaveAttribute('aria-live', 'off')
    await expectClean(page)
  })
})

test.describe('keyboard approval', { tag: ['@a11y'] }, () => {
  test.use({ storageState: { cookies: [], origins: [] }, viewport: { width: 1280, height: 800 } })

  test('an operator can sign in, open a ticket and approve from the keyboard', async ({ page }) => {
    test.setTimeout(60_000)
    await page.goto('/login')
    await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
    await focusByTab(page, page.getByLabel('Email'))
    await page.keyboard.type('op1@excellence.qai.local')
    await page.keyboard.press('Tab')
    await expect(page.getByLabel('Password')).toBeFocused()
    await page.keyboard.type(E2E_PASSWORD)
    await page.keyboard.press('Tab')
    await expect(page.getByRole('button', { name: 'Sign in', exact: true })).toBeFocused()
    await page.keyboard.press('Enter')
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 20_000 })

    await focusByTab(page, page.getByRole('link', { name: 'Tickets', exact: true }))
    await page.keyboard.press('Enter')
    await expect(page.getByRole('heading', { name: 'Tickets' })).toBeVisible()

    await focusByTab(page, page.getByRole('row', { name: /Invoice template logo looks blurry/ }), 60)
    await page.keyboard.press('Enter')
    await expect(page.getByRole('heading', { name: 'AI summary' })).toBeVisible()

    await focusByTab(page, page.getByTestId('start-working'), 40)
    await page.keyboard.press('Enter')
    await expect(page.getByRole('heading', { name: 'Review draft' })).toBeVisible()
    await expectClean(page)
    await focusByTab(page, page.getByTestId('draft-approve'), 40)
    await page.keyboard.press('Enter')
    await expect(page.getByTestId('draft-editor')).toHaveCount(0)
  })
})

async function focusByTab(page: Page, target: Locator, max = 30) {
  for (let step = 0; step < max; step += 1) {
    if (await target.evaluate(element => element === document.activeElement).catch(() => false)) return
    await page.keyboard.press('Tab')
  }
  await expect(target).toBeFocused()
}

async function expectClean(page: Page) {
  const results = await new AxeBuilder({ page }).exclude('nuxt-devtools-frame').analyze()
  const serious = results.violations.filter(item => item.impact === 'serious' || item.impact === 'critical')
  expect(serious, JSON.stringify(serious.map(item => item.id), null, 2)).toEqual([])
}
