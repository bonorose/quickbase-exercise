import { expect, test } from '@playwright/test'
import { E2E_PASSWORD, QUANTUM_EMAIL, loginThroughUi } from './fixtures/auth'

test.describe('tenancy', { tag: ['@tenancy'] }, () => {
  test('header badge matches each organization, and a user switch does not leak data', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByTestId('tenant-badge')).toHaveText(/Excellence/i)
    await expect(page.getByTestId('tenant-badge')).not.toHaveText(/Quantum/i)

    await page.getByRole('button', { name: /sign out/i }).click()
    await loginThroughUi(page, QUANTUM_EMAIL, E2E_PASSWORD)
    await expect(page.getByTestId('tenant-badge')).toHaveText(/Quantum/i)
    await expect(page.getByTestId('tenant-badge')).not.toHaveText(/Excellence/i)
    // An Excellence-only string (the SSO incident tickets) must never reach a Quantum session.
    await expect(page.locator('body')).not.toContainText('AADSTS50008')
  })

  test('an expired session returns to login with the redirect preserved', async ({ page, context }) => {
    await context.clearCookies()
    await page.goto('/tickets')
    await expect(page).toHaveURL(/\/login\?redirect=/)
    expect(page.url()).toContain('redirect=')
  })
})
