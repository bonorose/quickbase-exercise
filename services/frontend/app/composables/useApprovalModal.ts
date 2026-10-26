import type { PendingRevision } from '~/types/api/responses'
import { chatReloadTick } from '~/composables/useChat'

/**
 * Chat approval gate. When a turn leaves an open draft, open a blocking review once the
 * stream has finished. The ticket only changes through Approve; "decide later" keeps the
 * draft open and moves it to a reminder bar instead of executing anything.
 */
export function useApprovalModal(pending: Ref<PendingRevision | null>, streaming: Ref<boolean>) {
  const { pendingRevisions } = useServices()
  const { role } = useAuth()
  const reloadTick = useState(chatReloadTick, () => 0)

  const draft = ref<PendingRevision | null>(null)
  const open = ref(false)
  const setAside = new Set<string>()
  let loading: string | null = null

  async function show(id: string) {
    loading = id
    try {
      // Always fetch: a reloaded session only knows the id, and expiry needs a fresh server_time.
      const fresh = await pendingRevisions.get(id)
      if (loading !== id) return
      if (fresh.status !== 'open') {
        draft.value = null
        open.value = false
        return
      }
      draft.value = fresh
      open.value = !setAside.has(id)
    }
    catch {
      // The trace's "Open draft" link still reaches it.
    }
    finally {
      if (loading === id) loading = null
    }
  }

  watch([() => pending.value?.id ?? null, streaming], ([id, isStreaming]) => {
    if (!id || isStreaming || setAside.has(id) || draft.value?.id === id) return
    void show(id)
  }, { immediate: true })

  const canApprove = computed(() => !draft.value?.tainted || role.value === 'team_lead')
  const needsLead = computed(() => !!draft.value?.tainted && role.value !== 'team_lead')
  const waiting = computed(() => draft.value != null && !open.value)

  function decideLater() {
    if (draft.value) setAside.add(draft.value.id)
    open.value = false
  }

  function reopen() {
    if (!draft.value) return
    setAside.delete(draft.value.id)
    void show(draft.value.id)
  }

  function onUpdated(next: PendingRevision) {
    draft.value = next
  }

  function onDecided(decided: PendingRevision) {
    setAside.add(decided.id)
    draft.value = null
    open.value = false
    // Reload the session so the trace shows the outcome and any other open draft comes up next.
    reloadTick.value += 1
  }

  return { draft, open, canApprove, needsLead, waiting, decideLater, reopen, onUpdated, onDecided }
}
