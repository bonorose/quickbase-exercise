import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mockNuxtImport } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import type { ChatSessionVM } from '~/services/chat.service'

const listSessions = vi.hoisted(() => vi.fn())

mockNuxtImport('useServices', () => {
  return () => ({
    chat: { listSessions },
  })
})

mockNuxtImport('useState', () => {
  return (_key: string, init?: () => unknown) => ref(init ? init() : undefined)
})

mockNuxtImport('useAsyncData', () => {
  return (_key: string, handler: () => Promise<unknown>) => {
    const data = ref<unknown>()
    const pending = ref(true)
    const error = ref<unknown>(null)
    const refresh = async () => {
      data.value = await handler()
      pending.value = false
    }
    void refresh()
    return { data, pending, error, refresh }
  }
})

function session(id: string): ChatSessionVM {
  return {
    id,
    title: `Session ${id}`,
    createdAt: new Date(1_700_000_000_000),
    lastActivityAt: new Date(1_700_000_100_000),
  }
}

describe('useChatSessions', () => {
  beforeEach(() => {
    listSessions.mockReset()
  })

  it('loads the first 20 sessions and requests offset=20 on Load more', async () => {
    const first = Array.from({ length: 20 }, (_, index) => session(`s${index}`))
    const next = Array.from({ length: 10 }, (_, index) => session(`s${20 + index}`))
    listSessions
      .mockResolvedValueOnce({ items: first, total: 30, limit: 20, offset: 0 })
      .mockResolvedValueOnce({ items: next, total: 30, limit: 20, offset: 20 })

    const { useChatSessions } = await import('~/composables/useChatSessions')
    const api = useChatSessions()
    await flushPromises()

    expect(listSessions).toHaveBeenCalledWith({ limit: 20, offset: 0 })
    expect(api.sessions.value).toHaveLength(20)
    expect(api.hasMore.value).toBe(true)

    await api.loadMore()
    expect(listSessions).toHaveBeenNthCalledWith(2, { limit: 20, offset: 20 })
    expect(api.sessions.value).toHaveLength(30)
    expect(api.hasMore.value).toBe(false)
  })
})
