import { expect, test } from '@playwright/test'

test.describe('mocked chat', { tag: '@mocks' }, () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test('search trace, stop control, and history survive reload', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Email').fill('op1@excellence.qai.local')
    await page.getByLabel('Password').fill('admin123')
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.getByRole('link', { name: 'Chat' }).click()
    await expect(page.getByRole('heading', { name: 'Chat', exact: true })).toBeVisible()

    await page.getByRole('button', { name: 'What\'s blocked on billing?' }).click()
    await page.getByTestId('chat-composer').fill('What\'s blocked on billing?')
    await page.getByTestId('chat-send').click()
    await expect(page.getByTestId('tool-trace')).toContainText('Searched tickets')
    await expect(page.getByText('I found a billing ticket.')).toBeVisible()
    await expect(page).toHaveURL(/\/chat\//)

    const url = page.url()
    await page.reload()
    await expect(page).toHaveURL(url)
    await expect(page.getByTestId('tool-trace')).toContainText('Searched tickets')
    await page.getByTestId('tool-trace').getByRole('button').click()
    await expect(page.getByRole('link', { name: 'Excellence ticket 4 billing' })).toHaveAttribute('href', /\/tickets\?id=4/)
  })

  test('stop keeps the partial answer', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Email').fill('op1@excellence.qai.local')
    await page.getByLabel('Password').fill('admin123')
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.getByRole('link', { name: 'Chat' }).click()
    await expect(page.getByRole('heading', { name: 'Chat', exact: true })).toBeVisible()
    await page.getByTestId('chat-composer').fill('slow answer please')
    await page.getByTestId('chat-send').click()
    await expect(page.getByTestId('chat-stop')).toBeVisible()
    await page.getByTestId('chat-stop').click()
    await expect(page.getByText('Stopped')).toBeVisible()
    await expect(page.getByTestId('chat-send')).toBeVisible()
  })
})
