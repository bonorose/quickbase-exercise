import { defineConfig, devices } from '@playwright/test'
import { EXCELLENCE_STORAGE } from './e2e/fixtures/auth'

const skipBackend = process.env.E2E_SKIP_BACKEND === '1'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  workers: 2,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:3000',
    storageState: skipBackend ? undefined : EXCELLENCE_STORAGE,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  globalSetup: './e2e/global-setup.ts',
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
})
