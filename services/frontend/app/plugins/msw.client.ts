export default defineNuxtPlugin({
  name: 'msw',
  enforce: 'pre',
  async setup() {
    const { useMocks } = useRuntimeConfig().public
    if (!useMocks) return
    const { startMockWorker } = await import('../../mocks/browser')
    await startMockWorker()
  },
})
