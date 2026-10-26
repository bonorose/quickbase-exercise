import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatComposer from '~/components/chat/ChatComposer.vue'

function mountComposer(props: Partial<{ canSend: boolean, streaming: boolean, showExamples: boolean }> = {}) {
  return mount(ChatComposer, {
    props: { canSend: true, streaming: false, showExamples: false, ...props },
  })
}

describe('ChatComposer', () => {
  it('sends on Enter and keeps a newline for Shift+Enter', async () => {
    const wrapper = mountComposer()
    const field = wrapper.get('textarea')
    await field.setValue('hello')
    await field.trigger('keydown', { key: 'Enter', shiftKey: true })
    expect(wrapper.emitted('send')).toBeUndefined()
    await field.trigger('keydown', { key: 'Enter' })
    expect(wrapper.emitted('send')?.[0]).toEqual(['hello'])
  })

  it('refuses whitespace and caps the field at 4000 characters', async () => {
    const wrapper = mountComposer()
    await wrapper.get('textarea').setValue('   ')
    expect(wrapper.get('[data-testid="chat-send"]').attributes('disabled')).toBeDefined()
    expect(wrapper.get('textarea').attributes('maxlength')).toBe('4000')
    await wrapper.get('textarea').setValue('x'.repeat(3500))
    expect(wrapper.text()).toContain('3500 / 4000')
  })

  it('turns Send into Stop while streaming and stays usable with a pending draft', async () => {
    const streaming = mountComposer({ streaming: true, canSend: false })
    await streaming.get('textarea').setValue('hi')
    await streaming.get('textarea').trigger('keydown', { key: 'Enter' })
    expect(streaming.emitted('send')).toBeUndefined()
    await streaming.get('[data-testid="chat-stop"]').trigger('click')
    expect(streaming.emitted('stop')).toHaveLength(1)
    expect(streaming.get('textarea').attributes('disabled')).toBeUndefined()
  })
})
