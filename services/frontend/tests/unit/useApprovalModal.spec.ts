import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mockNuxtImport } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import type { PendingRevision } from '~/types/api/responses'
import { useApprovalModal } from '~/composables/useApprovalModal'

const get = vi.hoisted(() => vi.fn())
const role = vi.hoisted(() => ({ value: 'operator' as string }))
const states = vi.hoisted(() => new Map<string, { value: unknown }>())

mockNuxtImport('useServices', () => {
  return () => ({ pendingRevisions: { get } })
})

mockNuxtImport('useAuth', () => {
  return () => ({ role: computed(() => role.value) })
})

mockNuxtImport('useState', () => {
  return (key: string, init?: () => unknown) => {
    if (!states.has(key)) states.set(key, ref(init ? init() : undefined))
    return states.get(key)
  }
})

function draft(overrides: Partial<PendingRevision> = {}): PendingRevision {
  return {
    id: 'd1',
    ticket: { id: 7, title: 'VPN drops during standup' },
    action: 'update',
    origin: 'agent',
    owner: { id: 1, name: 'Operator One' },
    session_id: 's1',
    previous_revision_id: null,
    changed_contents: { priority: 'lowest' },
    diff: { priority: { from: 'high', to: 'lowest' } },
    tainted: false,
    status: 'open',
    expires_at: 1_700_000_600,
    server_time: 1_700_000_000,
    decided_by: null,
    decided_at: null,
    date_created: 1_700_000_000,
    date_updated: 1_700_000_000,
    result: null,
    ...overrides,
  }
}

function setup(streamingAtStart = false) {
  const pending = ref<PendingRevision | null>(null)
  const streaming = ref(streamingAtStart)
  const modal = useApprovalModal(pending, streaming)
  return { pending, streaming, modal }
}

describe('useApprovalModal', () => {
  beforeEach(() => {
    get.mockReset()
    role.value = 'operator'
    states.clear()
  })

  it('waits for the turn to finish streaming, then opens with a fresh copy of the draft', async () => {
    get.mockResolvedValue(draft())
    const { pending, streaming, modal } = setup(true)
    pending.value = draft()
    await flushPromises()
    expect(get).not.toHaveBeenCalled()
    expect(modal.open.value).toBe(false)

    streaming.value = false
    await flushPromises()
    expect(get).toHaveBeenCalledWith('d1')
    expect(modal.open.value).toBe(true)
    expect(modal.draft.value?.id).toBe('d1')
  })

  it('opens for an id-only draft found when a session is reloaded', async () => {
    get.mockResolvedValue(draft())
    const { pending, modal } = setup()
    pending.value = { id: 'd1' } as PendingRevision
    await flushPromises()
    expect(modal.open.value).toBe(true)
  })

  it('does not open for a draft that is no longer open', async () => {
    get.mockResolvedValue(draft({ status: 'expired' }))
    const { pending, modal } = setup()
    pending.value = draft()
    await flushPromises()
    expect(modal.open.value).toBe(false)
    expect(modal.draft.value).toBeNull()
  })

  it('lets the owner approve an untainted draft', async () => {
    get.mockResolvedValue(draft())
    const { pending, modal } = setup()
    pending.value = draft()
    await flushPromises()
    expect(modal.canApprove.value).toBe(true)
    expect(modal.needsLead.value).toBe(false)
  })

  it('does not let an operator approve a tainted draft', async () => {
    get.mockResolvedValue(draft({ tainted: true }))
    const { pending, modal } = setup()
    pending.value = draft({ tainted: true })
    await flushPromises()
    expect(modal.open.value).toBe(true)
    expect(modal.canApprove.value).toBe(false)
    expect(modal.needsLead.value).toBe(true)
  })

  it('lets a team lead approve a tainted draft', async () => {
    role.value = 'team_lead'
    get.mockResolvedValue(draft({ tainted: true }))
    const { pending, modal } = setup()
    pending.value = draft({ tainted: true })
    await flushPromises()
    expect(modal.canApprove.value).toBe(true)
    expect(modal.needsLead.value).toBe(false)
  })

  it('"decide later" closes without deciding, and the draft can be reopened', async () => {
    get.mockResolvedValue(draft())
    const { pending, streaming, modal } = setup()
    pending.value = draft()
    await flushPromises()

    modal.decideLater()
    expect(modal.open.value).toBe(false)
    expect(modal.waiting.value).toBe(true)

    // Another turn finishing does not force the same draft back open.
    streaming.value = true
    streaming.value = false
    await flushPromises()
    expect(modal.open.value).toBe(false)

    modal.reopen()
    await flushPromises()
    expect(modal.open.value).toBe(true)
    expect(get).toHaveBeenCalledTimes(2)
  })

  it('a decision closes the modal and reloads the session', async () => {
    get.mockResolvedValue(draft())
    const { pending, modal } = setup()
    pending.value = draft()
    await flushPromises()

    modal.onDecided(draft({ status: 'executed' }))
    expect(modal.open.value).toBe(false)
    expect(modal.draft.value).toBeNull()
    expect(modal.waiting.value).toBe(false)
    expect(states.get('chat:reload')?.value).toBe(1)
  })
})
