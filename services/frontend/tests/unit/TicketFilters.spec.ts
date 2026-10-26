import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import TicketFilters from '~/components/tickets/TicketFilters.vue'

describe('TicketFilters', () => {
  it('exposes labelled search and select triggers', () => {
    const wrapper = mount(TicketFilters, {
      props: { q: '', sort: '-date_updated' },
    })
    expect(wrapper.get('#ticket-search').attributes('type')).toBe('search')
    expect(wrapper.get('#ticket-status').text()).toContain('All')
    expect(wrapper.get('#ticket-priority').text()).toContain('All')
    expect(wrapper.get('#ticket-sort').text()).toContain('Updated (newest)')
    expect(wrapper.text()).toContain('Status')
    expect(wrapper.text()).toContain('Priority')
    expect(wrapper.text()).toContain('Sort')
  })
})
