import { computed } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import TicketDrawer from '~/components/tickets/TicketDrawer.vue'
import type { TicketDetail } from '~/types/models'

const state = vi.hoisted(() => ({
  ticket: null as TicketDetail | null,
  notFound: false,
}))

vi.mock('~/composables/useTicketDetail', () => ({
  useTicketDetail: () => ({
    ticket: computed(() => state.ticket),
    loading: computed(() => false),
    notFound: computed(() => state.notFound),
    errorMessage: computed(() => null),
    refresh: async () => {},
  }),
}))

const longDescription = `${'x'.repeat(20_040)}TAIL`

const ticket: TicketDetail = {
  id: 12,
  status: 'open',
  priority: 'low',
  title: 'Billing export fails',
  description: longDescription,
  contents: 'Client markdown',
  submittedBy: 'client@example.com',
  createdAt: new Date('2026-10-25T12:00:00Z'),
  updatedByName: null,
  updatedAt: new Date('2026-10-25T13:00:00Z'),
  revisions: [],
  discussions: [],
  openDraft: null,
}

const stubs = {
  Sheet: { template: '<div><slot /></div>' },
  SheetContent: { template: '<div><slot /></div>' },
  SheetHeader: { template: '<div><slot /></div>' },
  SheetTitle: { template: '<h2><slot /></h2>' },
  SheetDescription: { template: '<div><slot /></div>' },
  Skeleton: { template: '<div />' },
  Alert: { template: '<div><slot /></div>' },
  AlertDescription: { template: '<div><slot /></div>' },
  Badge: { template: '<span><slot /></span>' },
  StatusBadge: { template: '<span />' },
  PriorityBadge: { template: '<span />' },
  RevisionTimeline: { template: '<div />' },
  DiscussionList: { template: '<div />' },
  NuxtLink: { template: '<a><slot /></a>' },
}

describe('TicketDrawer', () => {
  it('renders ticket 12 and a truncated long description', () => {
    state.ticket = ticket
    state.notFound = false
    const wrapper = mount(TicketDrawer, {
      props: { ticketId: 12 },
      global: { stubs },
    })
    expect(wrapper.text()).toContain('#12')
    expect(wrapper.text()).toContain('Billing export fails')
    expect(wrapper.text()).toContain('AI summary')
    expect(wrapper.text()).toContain('Former member')
    expect(wrapper.text()).toContain('(truncated)')
    expect(wrapper.text()).not.toContain('TAIL')
  })

  it('shows the shared not-found state for a missing ticket', () => {
    state.ticket = null
    state.notFound = true
    const wrapper = mount(TicketDrawer, {
      props: { ticketId: 101 },
      global: { stubs },
    })
    expect(wrapper.get('[data-testid="not-found-state"]').text()).toContain('couldn\'t find that ticket')
    expect(wrapper.text().toLowerCase()).not.toContain('permission')
    expect(wrapper.text().toLowerCase()).not.toContain('organization')
  })
})
