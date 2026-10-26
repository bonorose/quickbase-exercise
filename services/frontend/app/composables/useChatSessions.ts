import type { ChatSessionVM } from '~/services/chat.service'
import { chatSessionsTick } from '~/composables/useChat'

const PAGE_SIZE = 20

/** The caller's sessions, newest activity first. Refreshes when a turn finishes. */
export function useChatSessions() {
  const { chat } = useServices()
  const tick = useState(chatSessionsTick, () => 0)
  const extra = ref<ChatSessionVM[]>([])

  const query = useAsyncData(
    'chat:sessions',
    () => chat.listSessions({ limit: PAGE_SIZE, offset: 0 }),
    { watch: [tick] },
  )

  watch(tick, () => {
    extra.value = []
  })

  const sessions = computed(() => {
    const first = query.data.value?.items ?? []
    const seen = new Set(first.map(session => session.id))
    return [...first, ...extra.value.filter(session => !seen.has(session.id))]
  })

  const total = computed(() => query.data.value?.total ?? 0)
  const hasMore = computed(() => sessions.value.length < total.value)
  const loadingMore = ref(false)

  async function loadMore() {
    if (!hasMore.value || loadingMore.value) return
    loadingMore.value = true
    try {
      const page = await chat.listSessions({ limit: PAGE_SIZE, offset: sessions.value.length })
      extra.value = [...extra.value, ...page.items]
    }
    finally {
      loadingMore.value = false
    }
  }

  return {
    sessions,
    total,
    hasMore,
    loadingMore,
    pending: query.pending,
    error: query.error,
    refresh: query.refresh,
    loadMore,
  }
}
