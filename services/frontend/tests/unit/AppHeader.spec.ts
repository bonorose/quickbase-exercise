import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { computed } from 'vue'
import AppHeader from '~/components/layout/AppHeader.vue'

vi.mock('~/composables/useAuth', () => ({
  useAuth: () => ({
    user: computed(() => ({
      id: 22,
      email: 'op1@quantum.qai.local',
      fullName: 'Quantum Operator One',
      initials: 'QO',
      role: 'operator',
      organization: { id: 2, name: 'Quantum Workflow' },
    })),
    organization: computed(() => ({ id: 2, name: 'Quantum Workflow' })),
    role: computed(() => 'operator'),
    logout: vi.fn(),
  }),
}))

describe('AppHeader', () => {
  it('shows the organization badge and role', () => {
    const wrapper = mount(AppHeader, {
      global: {
        stubs: {
          NuxtLink: { template: '<a><slot /></a>' },
          Button: { template: '<button><slot /></button>' },
          Badge: { template: '<div data-testid="tenant-badge"><slot /></div>' },
          TooltipProvider: { template: '<div><slot /></div>' },
          Tooltip: { template: '<div><slot /></div>' },
          TooltipTrigger: { template: '<div><slot /></div>' },
          TooltipContent: { template: '<div><slot /></div>' },
        },
      },
    })
    expect(wrapper.get('[data-testid="tenant-badge"]').text()).toContain('Quantum Workflow')
    expect(wrapper.text()).toContain('Operator')
  })
})
