import { expect, test as base } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

export const E2E_PASSWORD = process.env.SEED_USER_PASSWORD ?? process.env.E2E_USER_PASSWORD ?? 'admin123'
export const E2E_USER_EMAIL = process.env.E2E_USER_EMAIL ?? 'op1@excellence.qai.local'
export const EXCELLENCE_EMAIL = process.env.E2E_EXCELLENCE_EMAIL ?? 'op1@excellence.qai.local'
export const QUANTUM_EMAIL = process.env.E2E_QUANTUM_EMAIL ?? 'op1@quantum.qai.local'

export const AUTH_DIR = path.join(import.meta.dirname, '..', '.auth')
export const EXCELLENCE_STORAGE = path.join(AUTH_DIR, 'excellence.json')
export const QUANTUM_STORAGE = path.join(AUTH_DIR, 'quantum.json')

export async function loginThroughUi(
  page: import('@playwright/test').Page,
  email: string,
  password = E2E_PASSWORD,
) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: /sign in/i }).click()
  await expect(page).not.toHaveURL(/\/login/, { timeout: 20_000 })
}

export async function writeAuthStorage(
  browser: import('@playwright/test').Browser,
  email: string,
  file: string,
  baseURL: string,
) {
  fs.mkdirSync(AUTH_DIR, { recursive: true })
  const context = await browser.newContext({ baseURL })
  const page = await context.newPage()
  await loginThroughUi(page, email)
  await context.storageState({ path: file })
  await context.close()
  return file
}

export async function prepareAuthStorage(
  browser: import('@playwright/test').Browser,
  baseURL: string,
) {
  await writeAuthStorage(browser, EXCELLENCE_EMAIL, EXCELLENCE_STORAGE, baseURL)
  await writeAuthStorage(browser, QUANTUM_EMAIL, QUANTUM_STORAGE, baseURL)
}

export const test = base.extend<{ excellenceStorage: string, quantumStorage: string }>({
  excellenceStorage: [async ({}, use) => {
    await use(EXCELLENCE_STORAGE)
  }, { scope: 'worker' }],
  quantumStorage: [async ({}, use) => {
    await use(QUANTUM_STORAGE)
  }, { scope: 'worker' }],
})
