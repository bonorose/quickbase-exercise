import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DiscussionList from '~/components/tickets/DiscussionList.vue'
import { INJECTION_HTML, INJECTION_MARKDOWN } from '../../mocks/fixtures/tickets'

describe('DiscussionList', () => {
  it('renders discussions in id order with author names', () => {
    const wrapper = mount(DiscussionList, {
      props: {
        discussions: [
          { id: 2, authorName: 'Pat', contents: 'Second' },
          { id: 1, authorName: 'Kim', contents: 'First' },
        ],
      },
    })
    const authors = wrapper.findAll('li p').map(node => node.text())
    expect(authors).toEqual(['Pat', 'Kim'])
  })

  it('keeps injection payloads inert', () => {
    const wrapper = mount(DiscussionList, {
      props: {
        discussions: [
          { id: 1, authorName: 'Pat', contents: INJECTION_HTML },
          { id: 2, authorName: 'Kim', contents: INJECTION_MARKDOWN },
        ],
      },
    })
    expect(wrapper.html()).toContain('&lt;img src=x onerror=alert(1)&gt;')
    expect(wrapper.html()).not.toContain('<img src=x')
    expect(wrapper.text()).toContain(INJECTION_MARKDOWN)
    expect(wrapper.html()).not.toContain('<img')
  })
})
