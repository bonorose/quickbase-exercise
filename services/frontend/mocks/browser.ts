import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'

export async function startMockWorker() {
  const worker = setupWorker(...handlers)
  await worker.start({
    quiet: true,
    onUnhandledFrame: 'bypass',
    serviceWorker: { url: '/mockServiceWorker.js' },
  })
  return worker
}
