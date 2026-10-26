import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ToolCallTrace from '~/components/chat/ToolCallTrace.vue'
import type { ChatToolPartVM } from '~/services/chat.service'

function part(overrides: Partial<ChatToolPartVM> = {}): ChatToolPartVM {
  return {
    kind: 'tool',
    call_id: 'c1',
    name: 'search_tickets',
    args: { query: 'billing' },
    ...overrides,
  }
}

describe('ToolCallTrace', () => {
  it('shows a running search collapsed, then the error, and keeps injection text inert', async () => {
    const running = mount(ToolCallTrace, { props: { part: part() } })
    expect(running.text()).toContain('Searched tickets')
    expect(running.text()).toContain('Running…')
    expect(running.text()).not.toContain('Requested arguments')

    const failed = mount(ToolCallTrace, {
      props: { part: part({ ok: false, error: '<img src=x onerror=alert(1)>' }) },
    })
    expect(failed.text()).toContain('Failed')
    await failed.get('button').trigger('click')
    expect(failed.text()).toContain('Requested arguments')
    expect(failed.html()).toContain('&lt;img src=x onerror=alert(1)&gt;')
    expect(failed.html()).not.toContain('<img src=x')
  })

  it('links ticket ids from a search result', async () => {
    const wrapper = mount(ToolCallTrace, {
      props: {
        part: part({
          ok: true,
          result: { count: 1, tickets: [{ id: 4, title: 'Billing export fails', status: 'blocked', priority: 'high' }] },
        }),
      },
      global: { stubs: { NuxtLink: { props: ['to'], template: '<a :href="to"><slot /></a>' } } },
    })
    await wrapper.get('button').trigger('click')
    const link = wrapper.get('a')
    expect(link.attributes('href') ?? link.attributes('to')).toContain('/tickets?id=4')
    expect(link.text()).toContain('Billing export fails')
  })
})
