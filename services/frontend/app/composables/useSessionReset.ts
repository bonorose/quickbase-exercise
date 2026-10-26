import { getActivePinia } from 'pinia'
import { abortAllRegistered } from '~/utils/abortRegistry'

const SESSION_STORAGE_PREFIX = 'qai:'

/** Drop cached data, abort streams, and reset non-auth stores so a user switch cannot leak team data. */
export function resetClientState(): void {
  if (import.meta.client) {
    try {
      clearNuxtData()
    }
    catch {
      // Nuxt may not be ready in isolated unit tests
    }

    const pinia = getActivePinia()
    if (pinia) {
      for (const store of pinia._s.values()) {
        if (store.$id === 'auth') continue
        store.$reset?.()
      }
    }

    abortAllRegistered()

    const keys: string[] = []
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i)
      if (key?.startsWith(SESSION_STORAGE_PREFIX)) keys.push(key)
    }
    for (const key of keys) sessionStorage.removeItem(key)
  }
}

export function useSessionReset() {
  return { resetClientState }
}
