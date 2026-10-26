import { expect, test } from '@playwright/test'
import { E2E_PASSWORD, E2E_USER_EMAIL } from './fixtures/auth'
import { loginOrSkip } from './helpers'

test.describe('smoke', { tag: '@smoke' }, () => {
  test.describe('signed out', () => {
    test.use({ storageState: { cookies: [], origins: [] } })

    test('unauthenticated deep link redirects to login', async ({ page }) => {
      await page.goto('/tickets')
      await expect(page.getByLabel('Email')).toBeVisible({ timeout: 20_000 })
      await expect(page).toHaveURL(/\/login\?redirect=/)
      expect(page.url()).toContain('redirect=')
    })

    test('login, dashboard, logout', async ({ page }) => {
      test.skip(!(await loginOrSkip(page, E2E_USER_EMAIL, E2E_PASSWORD)), 'Seeded users are not available on this backend yet')
      await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
      await page.getByRole('button', { name: /sign out/i }).click()
      await expect(page).toHaveURL(/\/login/)
    })
  })
})
