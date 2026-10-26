import type { ApiClient } from '~/api/client'
import type { LoginRequest } from '~/types/api/requests'
import type { TokenResponse, UserResponse } from '~/types/api/responses'

export function createAuthApi(client: ApiClient, prefix: string) {
  return {
    login: (body: LoginRequest) =>
      client.request<TokenResponse>(`${prefix}/auth/login`, { method: 'POST', body }),

    me: () => client.request<UserResponse>(`${prefix}/auth/me`),

    logout: () => client.request<void>(`${prefix}/auth/logout`, { method: 'POST' }),
  }
}

export type AuthApi = ReturnType<typeof createAuthApi>
