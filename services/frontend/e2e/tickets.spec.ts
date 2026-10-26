import { expect, test } from '@playwright/test'
import { QUANTUM_STORAGE } from './fixtures/auth'
import { chooseSelect, watchBlockedHosts } from './helpers'

test.describe('tickets', { tag: ['@tickets'] }, () => {
  test('search, filters, pagination and the drawer', async ({ page }) => {
    const leaked = watchBlockedHosts(page)

    await page.goto('/tickets')
    await expect(page.getByRole('heading', { name: 'Tickets' })).toBeVisible()
    await expect(page.getByText(/Page \d+ of \d+/)).toBeVisible()

    const empty = page.getByText('No tickets match these filters')
    if (await empty.isVisible().catch(() => false)) {
      test.skip(true, 'Ticket list is empty — C-03 seed data is not available')
    }

    await page.getByLabel('Search').fill('billing')
    await expect(page).toHaveURL(/q=billing/, { timeout: 10_000 })
    await chooseSelect(page, 'Status', 'Closed')
    await expect(page).toHaveURL(/status=closed/)

    const firstRow = page.locator('table tbody tr').first()
    if (!(await firstRow.isVisible().catch(() => false))) {
      test.skip(true, 'No ticket matched "billing" on this backend')
    }
    await firstRow.click()
    await expect(page).toHaveURL(/id=/)
    await expect(page.getByRole('heading', { name: 'AI summary' })).toBeVisible()
    expect(leaked).toEqual([])
  })

  test('Excellence ids do not overlap Quantum ids', async ({ page, browser }) => {
    await page.goto('/tickets')
    await expect(page.getByRole('heading', { name: 'Tickets' })).toBeVisible()
    const excellenceIds = (await page.locator('table tbody tr td:first-child').allTextContents())
      .map(text => text.trim())
      .filter(Boolean)
    if (excellenceIds.length === 0) {
      test.skip(true, 'Ticket list is empty — C-03 seed data is not available')
    }

    const other = await browser.newContext({
      storageState: QUANTUM_STORAGE,
      baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:3000',
    })
    const quantumPage = await other.newPage()
    await quantumPage.goto('/tickets')
    const quantumIds = (await quantumPage.locator('table tbody tr td:first-child').allTextContents())
      .map(text => text.trim())
      .filter(Boolean)
    const overlap = excellenceIds.filter(id => quantumIds.includes(id))
    expect(overlap).toEqual([])

    if (quantumIds[0]) {
      await page.goto(`/tickets?id=${quantumIds[0]}`)
      await expect(page.getByTestId('not-found-state')).toBeVisible()
      await expect(page.locator('body')).not.toContainText(/permission|another team|organization/i)
    }
    await other.close()
  })

  test('narrow viewport still shows navigation', async ({ page }) => {
    await page.setViewportSize({ width: 800, height: 900 })
    await page.goto('/tickets')
    await page.getByRole('button', { name: 'Open navigation' }).click()
    await expect(page.getByRole('navigation', { name: 'Main' })).toBeVisible()
  })

  test('injection contents stay inert in the drawer', async ({ browser }) => {
    // The markdown-exfiltration ticket belongs to the Quantum team ("Our status badge image does not load").
    const quantum = await browser.newContext({
      storageState: QUANTUM_STORAGE,
      baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:3000',
    })
    const page = await quantum.newPage()
    const leaked = watchBlockedHosts(page)
    await page.goto('/tickets')
    await page.getByLabel('Search').fill('status badge')
    await expect(page).toHaveURL(/q=status/, { timeout: 10_000 })
    const firstRow = page.locator('table tbody tr').first()
    if (!(await firstRow.isVisible().catch(() => false))) {
      test.skip(true, 'Seeded injection ticket is not available')
    }
    await firstRow.click()
    await expect(page.getByRole('heading', { name: 'AI summary' })).toBeVisible()
    await expect(page.getByText(/attacker\.tld/).first()).toBeVisible()
    expect(leaked).toEqual([])
    await expect(page.locator('img[src*="attacker.tld"]')).toHaveCount(0)
    await quantum.close()
  })
})
