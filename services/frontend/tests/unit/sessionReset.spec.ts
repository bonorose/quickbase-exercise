import { describe, expect, it, vi } from 'vitest'
import { abortAllRegistered, registerAbortController } from '~/utils/abortRegistry'

describe('abortRegistry', () => {
  it('aborts every registered controller', () => {
    const first = new AbortController()
    const second = new AbortController()
    registerAbortController(first)
    registerAbortController(second)
    abortAllRegistered()
    expect(first.signal.aborted).toBe(true)
    expect(second.signal.aborted).toBe(true)
  })

  it('does not throw when aborting twice', () => {
    abortAllRegistered()
    expect(() => abortAllRegistered()).not.toThrow()
  })
})

describe('resetClientState sessionStorage prefix', () => {
  it('removes only qai: keys', () => {
    const store = new Map<string, string>([
      ['qai:cache', '1'],
      ['other', '2'],
    ])
    vi.stubGlobal('sessionStorage', {
      get length() { return store.size },
      key: (index: number) => [...store.keys()][index] ?? null,
      removeItem: (key: string) => { store.delete(key) },
    })
    const keys: string[] = []
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i)
      if (key?.startsWith('qai:')) keys.push(key)
    }
    for (const key of keys) sessionStorage.removeItem(key)
    expect(store.has('qai:cache')).toBe(false)
    expect(store.has('other')).toBe(true)
    vi.unstubAllGlobals()
  })
})
