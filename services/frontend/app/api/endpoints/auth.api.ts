import type { ApiClient } from '~/api/client'
import type { LoginRequest } from '~/types/api/requests'
import type { TokenResponse, UserResponse } from '~/types/api/responses'

export function createAuthApi(client: ApiClient, prefix: string) {
  return {
    login: (body: LoginRequest) =>
      client<TokenResponse>(`${prefix}/auth/login`, { method: 'POST', body }),

    /** Pass `token` to call before it is stored in the session (right after login). */
    me: (token?: string) =>
      client<UserResponse>(`${prefix}/auth/me`, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      }),
  }
}

export type AuthApi = ReturnType<typeof createAuthApi>
