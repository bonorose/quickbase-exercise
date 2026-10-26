import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import TicketsPagination from '~/components/tickets/TicketsPagination.vue'

describe('TicketsPagination', () => {
  it('shows the page and disables previous on the first page', async () => {
    const wrapper = mount(TicketsPagination, {
      props: { page: 1, pageCount: 3 },
    })
    expect(wrapper.text()).toContain('Page 1 of 3')
    const buttons = wrapper.findAll('button')
    expect(buttons[0]?.attributes('disabled')).toBeDefined()
    await buttons[1]?.trigger('click')
    expect(wrapper.emitted('go')?.[0]).toEqual([2])
  })
})
