import { mount, type ComponentMountingOptions } from '@vue/test-utils'
import type { Component } from 'vue'

export function createFakeServices(overrides: Record<string, unknown> = {}) {
  return {
    auth: {
      login: async () => ({ token: 't', user: null }),
      currentUser: async () => null,
    },
    dashboard: { getSummary: async () => null },
    chat: {
      createSession: async () => ({ id: 'sess-1', title: 'New conversation', createdAt: new Date(), lastActivityAt: new Date() }),
      listSessions: async () => ({ items: [], total: 0, limit: 20, offset: 0 }),
      getSession: async () => null,
      sendMessage: async function* () {},
    },
    llm: { streamCompletion: async function* () {} },
    tickets: { list: async () => ({ rows: [], total: 0, limit: 20, offset: 0 }), get: async () => null },
    ...overrides,
  }
}

export function mountWithPlugins(component: Component, options: ComponentMountingOptions<Component> = {}) {
  const services = (options.global?.provide as { $services?: unknown } | undefined)?.$services
    ?? createFakeServices()
  return mount(component, {
    ...options,
    global: {
      ...options.global,
      stubs: {
        NuxtLink: { template: '<a><slot /></a>' },
        ...options.global?.stubs,
      },
      provide: {
        ...options.global?.provide,
        $services: services,
      },
    },
  })
}
