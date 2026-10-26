import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import NotFoundState from '~/components/common/NotFoundState.vue'

describe('NotFoundState', () => {
  it('never mentions a team or permissions', () => {
    const wrapper = mount(NotFoundState, {
      props: { resource: 'ticket' },
      global: {
        stubs: {
          Button: { template: '<button><slot /></button>' },
          NuxtLink: { template: '<a><slot /></a>' },
        },
      },
    })
    const text = wrapper.text().toLowerCase()
    expect(text).toContain('couldn\'t find that ticket')
    expect(text).not.toContain('team')
    expect(text).not.toContain('permission')
    expect(text).not.toContain('organization')
  })
})
