import type { LoginCredentials } from '~/types/models'
import { MissingOrganizationError } from '~/services/auth.service'
import { resetClientState } from '~/composables/useSessionReset'

/** Auth orchestration: services (API) + store (state) + navigation. */
export function useAuth() {
  const store = useAuthStore()
  const { auth } = useServices()
  const lastUserId = useState<number | null>('auth-last-user-id', () => null)

  function rememberUser(id: number) {
    if (lastUserId.value != null && lastUserId.value !== id) {
      resetClientState()
    }
    lastUserId.value = id
  }

  async function login(credentials: LoginCredentials) {
    try {
      const user = await auth.login(credentials)
      rememberUser(user.id)
      store.setUser(user)
    }
    catch (err) {
      store.clearSession()
      if (err instanceof MissingOrganizationError) throw err
      throw err
    }
  }

  /** Load the user from the cookie session. Returns false when the user must sign in. */
  async function restoreSession(): Promise<boolean> {
    try {
      const user = await auth.currentUser()
      rememberUser(user.id)
      store.setUser(user)
      return true
    }
    catch {
      resetClientState()
      store.clearSession()
      lastUserId.value = null
      return false
    }
  }

  async function logout() {
    try {
      await auth.logout()
    }
    catch {
      // The local session is cleared even when the network call fails.
    }
    resetClientState()
    store.clearSession()
    lastUserId.value = null
    await navigateTo('/login')
  }

  return {
    user: computed(() => store.user),
    organization: computed(() => store.organization),
    role: computed(() => store.role),
    isAuthenticated: computed(() => store.isAuthenticated),
    login,
    logout,
    restoreSession,
  }
}
