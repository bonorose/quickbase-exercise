import { spawnSync } from 'node:child_process'
import path from 'node:path'
import { chromium } from '@playwright/test'
import { prepareAuthStorage } from './fixtures/auth'

const FRONTEND = process.env.E2E_BASE_URL ?? 'http://localhost:3000'
const API = process.env.E2E_API_BASE ?? 'http://localhost:5000'
const TIMEOUT_MS = 60_000
const REPO_ROOT = path.resolve(import.meta.dirname, '../../..')

async function waitFor(url: string, accept: (status: number) => boolean, label: string) {
  const started = Date.now()
  let lastError = 'no attempt'
  while (Date.now() - started < TIMEOUT_MS) {
    try {
      const response = await fetch(url, { redirect: 'manual' })
      if (accept(response.status)) return
      lastError = `HTTP ${response.status}`
    }
    catch (err) {
      lastError = err instanceof Error ? err.message : String(err)
    }
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
  throw new Error(`Timed out after ${TIMEOUT_MS / 1000}s waiting for ${label} (${url}): ${lastError}`)
}

function resetSeed() {
  if (process.env.E2E_SKIP_SEED === '1') return
  const result = spawnSync(
    'docker',
    ['compose', 'exec', '-T', 'backend', 'python', '-m', 'src.seed', '--reset'],
    { cwd: REPO_ROOT, encoding: 'utf8', shell: process.platform === 'win32' },
  )
  if (result.status !== 0) {
    const detail = [result.stderr, result.stdout, result.error?.message].filter(Boolean).join('\n')
    console.warn(`Seed reset skipped or failed: ${detail || `exit ${result.status}`}`)
  }
}

export default async function globalSetup() {
  await waitFor(FRONTEND, status => status >= 200 && status < 500, 'frontend')

  if (process.env.E2E_SKIP_BACKEND === '1') return

  try {
    await waitFor(`${API}/livez`, status => status === 200, 'backend /livez')
  }
  catch {
    await waitFor(`${API}/openapi.json`, status => status === 200, 'backend /openapi.json (livez unavailable)')
  }

  resetSeed()

  const browser = await chromium.launch()
  try {
    await prepareAuthStorage(browser, FRONTEND)
  }
  finally {
    await browser.close()
  }
}
