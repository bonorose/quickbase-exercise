/**
 * Dependency wiring (frontend counterpart of backend dependencies/providers.py):
 * api client -> endpoint modules -> services, exposed as `useNuxtApp().$services`.
 */
import { createApiClient } from '~/api/client'
import { createAuthApi } from '~/api/endpoints/auth.api'
import { createHealthApi } from '~/api/endpoints/health.api'
import { createItemsApi } from '~/api/endpoints/items.api'
import { AuthService } from '~/services/auth.service'
import { DashboardService } from '~/services/dashboard.service'

export default defineNuxtPlugin((nuxtApp) => {
  const { apiBase, apiPrefix } = useRuntimeConfig().public
  const authStore = useAuthStore()

  const client = createApiClient({
    baseURL: apiBase,
    getToken: () => authStore.token,
    onUnauthorized: () => {
      authStore.clearSession()
      void nuxtApp.runWithContext(() => navigateTo('/login'))
    },
  })

  const services = {
    auth: new AuthService(createAuthApi(client, apiPrefix)),
    dashboard: new DashboardService(createItemsApi(client, apiPrefix), createHealthApi(client)),
  }

  return { provide: { services } }
})
