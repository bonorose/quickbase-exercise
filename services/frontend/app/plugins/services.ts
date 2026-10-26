/**
 * Dependency wiring (frontend counterpart of the backend dependencies/ package):
 * api client -> endpoint modules -> services, exposed as `useNuxtApp().$services`.
 */
import { createApiClient } from '~/api/client'
import { useToast } from '~/composables/useToast'
import { createAuditApi } from '~/api/endpoints/audit.api'
import { createAuthApi } from '~/api/endpoints/auth.api'
import { createChatApi } from '~/api/endpoints/chat.api'
import { createHealthApi } from '~/api/endpoints/health.api'
import { createLLMApi } from '~/api/endpoints/llm.api'
import { createPendingRevisionsApi } from '~/api/endpoints/pendingRevisions.api'
import { createTicketsApi } from '~/api/endpoints/tickets.api'
import { AuthService } from '~/services/auth.service'
import { AuditService } from '~/services/audit.service'
import { ChatService } from '~/services/chat.service'
import { DashboardService } from '~/services/dashboard.service'
import { LLMService } from '~/services/llm.service'
import { PendingRevisionsService } from '~/services/pendingRevisions.service'
import { TicketsService } from '~/services/tickets.service'
import { resetClientState } from '~/composables/useSessionReset'

export default defineNuxtPlugin((nuxtApp) => {
  const { apiBase, apiPrefix } = useRuntimeConfig().public
  const authStore = useAuthStore()

  const { error } = useToast()
  const client = createApiClient({
    baseURL: apiBase,
    onUnauthorized: () => {
      error('Your session expired. Please sign in again')
      resetClientState()
      authStore.clearSession()
      const path = `${window.location.pathname}${window.location.search}`
      if (path.startsWith('/login')) return
      void nuxtApp.runWithContext(() => navigateTo({ path: '/login', query: { redirect: path } }))
    },
    onCsrfFailure: () => {
      error('Your session is invalid, please sign in again')
      resetClientState()
      authStore.clearSession()
      void nuxtApp.runWithContext(() => navigateTo('/login'))
    },
  })

  const ticketsApi = createTicketsApi(client, apiPrefix)

  const services = {
    auth: new AuthService(createAuthApi(client, apiPrefix)),
    dashboard: new DashboardService(ticketsApi, createHealthApi(client)),
    chat: new ChatService(createChatApi(client, apiPrefix)),
    llm: new LLMService(createLLMApi(client, apiPrefix)),
    tickets: new TicketsService(ticketsApi),
    pendingRevisions: new PendingRevisionsService(createPendingRevisionsApi(client, apiPrefix)),
    audit: new AuditService(createAuditApi(client, apiPrefix)),
  }

  return { provide: { services } }
})
