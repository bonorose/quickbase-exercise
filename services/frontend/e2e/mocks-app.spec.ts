import { expect, test } from '@playwright/test'

test.describe('mocked app', { tag: '@mocks' }, () => {
  test.use({ storageState: { cookies: [], origins: [] } })
  test('login, team badge, tickets and injection text stay inert', async ({ page }) => {
    const leaked: string[] = []
    page.on('request', (request) => {
      if (request.url().includes('attacker.tld')) leaked.push(request.url())
    })

    await page.goto('/login')
    await page.getByLabel('Email').fill('op1@excellence.qai.local')
    await page.getByLabel('Password').fill('admin123')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
    await expect(page.getByTestId('tenant-badge')).toHaveText(/Excellence/i)

    await page.getByRole('link', { name: 'Tickets' }).click()
    await expect(page.getByRole('heading', { name: 'Tickets' })).toBeVisible()
    await page.getByLabel('Search').fill('billing')
    await expect(page).toHaveURL(/q=billing/, { timeout: 10_000 })
    await page.locator('table tbody tr').first().click()
    await expect(page.getByRole('heading', { name: 'AI summary' })).toBeVisible()
    expect(leaked).toEqual([])

    await page.getByRole('button', { name: 'Close' }).click()
    await page.getByRole('button', { name: /sign out/i }).click()
    await page.getByLabel('Email').fill('op1@quantum.qai.local')
    await page.getByLabel('Password').fill('admin123')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page.getByTestId('tenant-badge')).toHaveText(/Quantum/i)
    await expect(page.locator('body')).not.toContainText('Excellence ticket')
  })
})
