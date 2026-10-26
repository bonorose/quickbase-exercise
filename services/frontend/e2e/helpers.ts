import { expect, type Page } from '@playwright/test'

/** Skip the rest of this test when D-01 users are not seeded yet. */
export async function loginOrSkip(page: Page, email: string, password: string) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: /sign in/i }).click()

  try {
    await page.waitForURL(url => !url.pathname.startsWith('/login'), { timeout: 20_000 })
    return true
  }
  catch {
    return false
  }
}

export async function chooseSelect(page: Page, label: string, option: string) {
  await page.getByLabel(label).click()
  await page.getByRole('option', { name: option, exact: true }).click()
}

export function watchBlockedHosts(page: Page) {
  const leaked: string[] = []
  page.on('request', (request) => {
    if (/attacker\.tld|evil\.example/i.test(request.url())) leaked.push(request.url())
  })
  return leaked
}

const API = process.env.E2E_API_BASE ?? 'http://localhost:5000'

export async function api(page: Page, method: string, path: string, data?: unknown) {
  const cookies = await page.context().cookies()
  const session = cookies.find(cookie => cookie.name === 'qb_session')?.value
  const csrf = cookies.find(cookie => cookie.name === 'qb_csrf')?.value
  const headers: Record<string, string> = {}
  if (session) headers.cookie = `qb_session=${session}; qb_csrf=${csrf ?? ''}`
  if (csrf && method !== 'GET') headers['x-csrf-token'] = csrf
  return page.request.fetch(`${API}${path}`, { method, headers, data })
}

export async function firstTicketId(page: Page) {
  await page.goto('/tickets')
  const cell = page.locator('table tbody tr td').first()
  await expect(cell).toBeVisible({ timeout: 20_000 })
  return (await cell.innerText()).trim()
}

export async function ticketState(page: Page, id: string) {
  const response = await api(page, 'GET', `/api/v1/tickets/${id}`)
  if (response.status() !== 200) throw new Error(`C-04 ${id} returned ${response.status()}`)
  return response.json() as Promise<{
    status: string
    priority: string
    contents: string
    title: string
    open_pending_revision: { id: string } | null
  }>
}

export async function claimableTicketId(page: Page) {
  await page.goto('/tickets')
  const rows = page.locator('table tbody tr')
  await expect(rows.first()).toBeVisible({ timeout: 20_000 })
  const count = await rows.count()
  const ids: string[] = []
  for (let i = 0; i < count; i++) {
    const id = (await rows.nth(i).locator('td').first().innerText()).trim()
    if (id) ids.push(id)
  }
  for (const id of ids) {
    const body = await ticketState(page, id)
    if (!body.open_pending_revision) return id
  }
  throw new Error('No claimable ticket on the first page')
}
