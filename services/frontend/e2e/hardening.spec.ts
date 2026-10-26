import { expect, test } from '@playwright/test'
import { E2E_PASSWORD, loginThroughUi } from './fixtures/auth'

const API = process.env.E2E_API_BASE ?? 'http://localhost:5000'
const LOGIN_LIMIT = Number(process.env.E2E_LOGIN_RATE_LIMIT ?? 10)

test.describe('hardening', { tag: ['@hardening'] }, () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test('login sets an httpOnly session cookie that survives reload and logout', async ({ page, context }) => {
    await loginThroughUi(page, 'op1@excellence.qai.local', E2E_PASSWORD)
    const cookies = await context.cookies()
    const session = cookies.find(cookie => cookie.name === 'qb_session')
    const csrf = cookies.find(cookie => cookie.name === 'qb_csrf')
    expect(session?.httpOnly).toBe(true)
    expect(csrf?.httpOnly).toBe(false)

    await page.reload()
    await expect(page.getByTestId('tenant-badge')).toBeVisible()

    await page.getByRole('button', { name: /sign out/i }).click()
    await expect(page).toHaveURL(/\/login/)
    const me = await page.request.get(`${API}/api/v1/auth/me`)
    expect(me.status()).toBe(401)
  })

  test('too many bad logins show the countdown', async ({ page }) => {
    await page.goto('/login')
    const email = `nobody-rate-${Date.now()}@example.com`
    for (let attempt = 0; attempt < LOGIN_LIMIT + 1; attempt += 1) {
      await page.getByLabel('Email').fill(email)
      await page.getByLabel('Password').fill('wrong-password')
      await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    }
    await expect(page.getByRole('alert').getByText(/Too many attempts\. Try again in \d+ s/)).toBeVisible()
    await expect(page.getByRole('button', { name: 'Sign in', exact: true })).toBeDisabled()
  })

  test('a cookie POST without the CSRF header is 403', async ({ page, context }) => {
    await loginThroughUi(page, 'op1@excellence.qai.local', E2E_PASSWORD)
    const session = (await context.cookies()).find(cookie => cookie.name === 'qb_session')
    expect(session?.value).toBeTruthy()
    const denied = await page.request.post(`${API}/api/v1/chat/sessions`, {
      headers: { cookie: `qb_session=${session?.value}` },
      data: { title: 'csrf probe' },
    })
    expect(denied.status()).toBe(403)
    expect(await denied.json()).toMatchObject({ detail: 'CSRF check failed' })
  })
})

test.describe('hardening chat', { tag: ['@hardening'] }, () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test('chat spam shows the composer countdown', async ({ page }) => {
    test.setTimeout(120_000)
    await loginThroughUi(page, 'op1@excellence.qai.local', E2E_PASSWORD)
    await page.goto('/chat')
    const composer = page.getByLabel('Message')
    for (let attempt = 0; attempt < 25; attempt += 1) {
      await composer.fill(`ping ${attempt}`)
      await page.getByRole('button', { name: 'Send' }).click()
      const limited = page.getByText(/sending messages too fast/i)
      if (await limited.isVisible().catch(() => false)) {
        await expect(page.getByRole('button', { name: 'Send' })).toBeDisabled()
        return
      }
      await expect(page.getByTestId('stream-status')).not.toHaveText('Thinking…', { timeout: 20_000 }).catch(() => undefined)
    }
    await expect(page.getByText(/sending messages too fast/i)).toBeVisible()
  })
})
