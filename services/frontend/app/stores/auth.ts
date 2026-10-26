import { defineStore } from 'pinia'
import type { User } from '~/types/models'

/**
 * Session state only. The JWT lives in the httpOnly qb_session cookie.
 * A leftover qb_auth_token cookie from earlier builds is deleted on load.
 */
export const useAuthStore = defineStore('auth', () => {
  const legacy = useCookie<string | null>('qb_auth_token', { path: '/' })
  legacy.value = null

  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => user.value != null)
  const organization = computed(() => user.value?.organization ?? null)
  const role = computed(() => user.value?.role ?? null)

  function setUser(newUser: User) {
    user.value = newUser
  }

  function clearSession() {
    user.value = null
  }

  function $reset() {
    clearSession()
  }

  return {
    user,
    isAuthenticated,
    organization,
    role,
    setUser,
    clearSession,
    $reset,
  }
})
