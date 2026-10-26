import type { TicketPriority, TicketSort, TicketStatus } from '~/types/api/responses'
import { getApiErrorMessage } from '~/utils/apiError'

const PAGE_SIZE = 20
const STATUSES: TicketStatus[] = ['open', 'blocked', 'closed']
const PRIORITIES: TicketPriority[] = ['lowest', 'low', 'medium', 'high', 'critical']
const SORTS: TicketSort[] = ['-date_updated', 'date_updated', 'priority', '-priority', 'id']

export function parseStatus(value: unknown): TicketStatus | undefined {
  return typeof value === 'string' && (STATUSES as string[]).includes(value)
    ? value as TicketStatus
    : undefined
}

export function parsePriority(value: unknown): TicketPriority | undefined {
  return typeof value === 'string' && (PRIORITIES as string[]).includes(value)
    ? value as TicketPriority
    : undefined
}

export function parseSort(value: unknown): TicketSort {
  return typeof value === 'string' && (SORTS as string[]).includes(value)
    ? value as TicketSort
    : '-date_updated'
}

export function parsePage(value: unknown): number {
  const n = Number(value)
  return Number.isInteger(n) && n > 0 ? n : 1
}

export function parseTicketId(value: unknown): number | null {
  const n = Number(value)
  return Number.isInteger(n) && n > 0 ? n : null
}

export function useTicketList() {
  const route = useRoute()
  const router = useRouter()
  const { tickets } = useServices()

  const qInput = ref(typeof route.query.q === 'string' ? route.query.q : '')
  const qDebounced = ref(qInput.value)
  let debounceHandle: ReturnType<typeof setTimeout> | null = null

  watch(qInput, (value) => {
    if (debounceHandle) clearTimeout(debounceHandle)
    debounceHandle = setTimeout(() => {
      qDebounced.value = value
    }, 300)
  })

  watch(() => route.query.q, (value) => {
    const next = typeof value === 'string' ? value : ''
    if (next !== qInput.value) {
      qInput.value = next
      qDebounced.value = next
    }
  })

  onScopeDispose(() => {
    if (debounceHandle) clearTimeout(debounceHandle)
  })

  const status = computed(() => parseStatus(route.query.status))
  const priority = computed(() => parsePriority(route.query.priority))
  const sort = computed(() => parseSort(route.query.sort))
  const page = computed(() => parsePage(route.query.page))
  const selectedId = computed(() => parseTicketId(route.query.id))

  const listKey = computed(() =>
    [qDebounced.value, status.value ?? '', priority.value ?? '', sort.value, page.value].join('|'),
  )

  async function replaceQuery(patch: Record<string, string | undefined>) {
    const query: Record<string, string> = {}
    for (const [key, raw] of Object.entries({ ...route.query, ...patch })) {
      if (raw === undefined || raw === '' || raw === null) continue
      const value = Array.isArray(raw) ? raw[0] : raw
      if (value == null || value === '') continue
      if (key === 'page' && value === '1') continue
      if (key === 'sort' && value === '-date_updated') continue
      query[key] = String(value)
    }
    await router.replace({ query })
  }

  watch(qDebounced, async (value) => {
    const current = typeof route.query.q === 'string' ? route.query.q : ''
    if (value === current) return
    await replaceQuery({ q: value || undefined, page: undefined })
  })

  const { data, status: loadStatus, error, refresh } = useAsyncData(
    () => `tickets:list:${listKey.value}`,
    () => tickets.list({
      q: qDebounced.value || undefined,
      status: status.value,
      priority: priority.value,
      sort: sort.value,
      limit: PAGE_SIZE,
      offset: (page.value - 1) * PAGE_SIZE,
    }),
    { watch: [listKey], dedupe: 'cancel' },
  )

  const rows = computed(() => data.value?.rows ?? [])
  const total = computed(() => data.value?.total ?? 0)
  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

  watch([total, page, loadStatus], async ([nextTotal, nextPage, nextStatus]) => {
    if (nextStatus !== 'success') return
    const last = Math.max(1, Math.ceil(nextTotal / PAGE_SIZE))
    if (nextPage > last) await replaceQuery({ page: last === 1 ? undefined : String(last) })
  })

  function setFilter(next: { status?: TicketStatus | '', priority?: TicketPriority | '', sort?: TicketSort }) {
    void replaceQuery({
      status: next.status === undefined ? (status.value ?? undefined) : (next.status || undefined),
      priority: next.priority === undefined ? (priority.value ?? undefined) : (next.priority || undefined),
      sort: next.sort,
      page: undefined,
    })
  }

  function goToPage(next: number) {
    const clamped = Math.min(Math.max(1, next), pageCount.value)
    void replaceQuery({ page: clamped === 1 ? undefined : String(clamped) })
  }

  function openTicket(id: number) {
    void replaceQuery({ id: String(id) })
  }

  function closeTicket() {
    void replaceQuery({ id: undefined })
  }

  function clearFilters() {
    qInput.value = ''
    qDebounced.value = ''
    void replaceQuery({
      q: undefined,
      status: undefined,
      priority: undefined,
      sort: undefined,
      page: undefined,
    })
  }

  return {
    qInput,
    status,
    priority,
    sort,
    page,
    pageCount,
    selectedId,
    rows,
    total,
    loading: computed(() => loadStatus.value === 'pending'),
    errorMessage: computed(() => error.value ? getApiErrorMessage(error.value, 'Could not load tickets.') : null),
    setFilter,
    goToPage,
    openTicket,
    closeTicket,
    clearFilters,
    refresh,
    pageSize: PAGE_SIZE,
  }
}
