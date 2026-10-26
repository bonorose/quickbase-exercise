/**
 * Threat: a deep link or rendered payload leaks another team or phones home.
 * Control: cross-org URLs are 404; injection text is inert; assistant echoes stay text.
 */
import { expect, test } from '@playwright/test'
import { E2E_PASSWORD, loginThroughUi, QUANTUM_EMAIL } from '../fixtures/auth'
import { api, firstTicketId, watchBlockedHosts } from '../helpers'

test.describe('adversarial tenancy and content', { tag: ['@adversarial'] }, () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test.beforeEach(async ({ page }) => {
    await loginThroughUi(page, 'op1@excellence.qai.local', E2E_PASSWORD)
  })
  test('an Excellence session cannot read a Quantum ticket, chat or audit row', async ({ page, browser }) => {
    const quantum = await browser.newContext({ storageState: { cookies: [], origins: [] } })
    const quantumPage = await quantum.newPage()
    await loginThroughUi(quantumPage, QUANTUM_EMAIL, E2E_PASSWORD)
    const foreignId = await firstTicketId(quantumPage)
    const created = await api(quantumPage, 'POST', '/api/v1/chat/sessions', { title: 'quantum private notes' })
    expect(created.status()).toBe(201)
    const sessionId = (await created.json()).id as string
    await quantum.close()

    await page.goto(`/tickets?id=${foreignId}`)
    await expect(page.getByTestId('not-found-state')).toBeVisible()
    const response = await api(page, 'GET', `/api/v1/tickets/${foreignId}`)
    expect(response.status()).toBe(404)
    const ticketText = await page.locator('body').innerText()
    expect(ticketText).not.toContain('SYSTEM OVERRIDE')
    expect(ticketText).not.toContain('quantum private notes')

    await page.goto(`/chat/${sessionId}`)
    await expect(page.getByTestId('not-found-state')).toBeVisible()
    expect(await page.locator('body').innerText()).not.toContain('quantum private notes')

    const lead = await browser.newContext({ storageState: { cookies: [], origins: [] } })
    const leadPage = await lead.newPage()
    await loginThroughUi(leadPage, 'lead@excellence.qai.local')
    await leadPage.goto('/audit')
    await leadPage.getByTestId('audit-ticket-filter').fill(foreignId)
    await leadPage.getByRole('button', { name: 'Filter' }).click()
    await expect(leadPage.getByTestId('not-found-state')).toBeVisible()
    expect(await leadPage.locator('body').innerText()).not.toContain('quantum private notes')
    await lead.close()
  })

  test('seeded injection text stays inert', async ({ page, browser }) => {
    // Excellence: the poisoned-summary ticket (instructions in the AI summary and the body) renders as text.
    const leaked = watchBlockedHosts(page)
    await page.goto('/tickets')
    await page.getByLabel('Search').fill('logo looks blurry')
    await expect(page).toHaveURL(/q=logo/, { timeout: 10_000 })
    await page.locator('table tbody tr').first().click()
    await expect(page.getByText(/IMPORTANT NOTE FOR THE AI ASSISTANT/).first()).toBeVisible()
    expect(leaked).toEqual([])

    // Quantum: the markdown-exfiltration ticket shows the image URL as text and never requests it.
    const quantum = await browser.newContext({ storageState: { cookies: [], origins: [] } })
    const quantumPage = await quantum.newPage()
    const quantumLeaked = watchBlockedHosts(quantumPage)
    await loginThroughUi(quantumPage, QUANTUM_EMAIL, E2E_PASSWORD)
    await quantumPage.goto('/tickets')
    await quantumPage.getByLabel('Search').fill('status badge')
    await expect(quantumPage).toHaveURL(/q=status/, { timeout: 10_000 })
    await quantumPage.locator('table tbody tr').first().click()
    await expect(quantumPage.getByText(/attacker\.tld/).first()).toBeVisible()
    await expect(quantumPage.locator('img[src*="attacker.tld"]')).toHaveCount(0)
    expect(quantumLeaked).toEqual([])
    await quantum.close()
  })

  test('an assistant echo of an injection stays inert', async ({ page }) => {
    const leaked = watchBlockedHosts(page)
    let dialogs = 0
    page.on('dialog', async (dialog) => {
      dialogs += 1
      await dialog.dismiss()
    })
    await page.goto('/chat')
    await page.getByTestId('chat-composer').fill('echo the injected image')
    await page.getByTestId('chat-send').click()
    await expect(page.getByText('[image removed]')).toBeVisible({ timeout: 20_000 })
    expect(leaked).toEqual([])
    expect(dialogs).toBe(0)
    await expect(page.locator('img[src*="evil.example"]')).toHaveCount(0)
  })
})
