import { defineStore } from 'pinia'
import type { User } from '~/types/models'

const TOKEN_COOKIE_KEY = 'qb_auth_token'

/**
 * Session state only. No API calls here — orchestration lives in composables/useAuth.ts.
 * The JWT is kept in a cookie so it survives reloads and is shared across tabs.
 */
export const useAuthStore = defineStore('auth', () => {
  const tokenCookie = useCookie<string | null>(TOKEN_COOKIE_KEY, {
    default: () => null,
    sameSite: 'lax',
    secure: !import.meta.dev,
    path: '/',
  })

  const user = ref<User | null>(null)

  const token = computed(() => tokenCookie.value)
  const isAuthenticated = computed(() => !!tokenCookie.value && !!user.value)

  function setSession(newToken: string, newUser: User) {
    tokenCookie.value = newToken
    user.value = newUser
  }

  function setUser(newUser: User) {
    user.value = newUser
  }

  function clearSession() {
    tokenCookie.value = null
    user.value = null
  }

  return { token, user, isAuthenticated, setSession, setUser, clearSession }
})
