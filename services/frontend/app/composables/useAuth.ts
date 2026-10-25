import type { LoginCredentials } from '~/types/models'
import { isJwtExpired } from '~/utils/jwt'

/** Auth orchestration: services (API) + store (state) + navigation. */
export function useAuth() {
  const store = useAuthStore()
  const { auth } = useServices()

  async function login(credentials: LoginCredentials) {
    const session = await auth.login(credentials)
    store.setSession(session.token, session.user)
  }

  /** Make sure a valid token has a loaded user. Returns false when the user must log in. */
  async function restoreSession(): Promise<boolean> {
    if (isJwtExpired(store.token)) {
      store.clearSession()
      return false
    }
    if (store.user) return true
    try {
      store.setUser(await auth.currentUser())
      return true
    }
    catch {
      store.clearSession()
      return false
    }
  }

  async function logout() {
    store.clearSession()
    await navigateTo('/login')
  }

  return {
    user: computed(() => store.user),
    isAuthenticated: computed(() => store.isAuthenticated),
    login,
    logout,
    restoreSession,
  }
}
