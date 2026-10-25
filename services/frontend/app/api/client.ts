/**
 * HTTP client — the only place that knows about base URL, auth header and 401 handling.
 * Endpoint modules in ./endpoints receive this client; nothing above the api/ layer calls $fetch.
 */
export type ApiClient = typeof $fetch

export interface ApiClientOptions {
  baseURL: string
  getToken: () => string | null
  onUnauthorized: () => void
}

export function createApiClient({ baseURL, getToken, onUnauthorized }: ApiClientOptions): ApiClient {
  return $fetch.create({
    baseURL,
    onRequest({ options }) {
      const token = getToken()
      if (token && !options.headers.has('Authorization')) {
        options.headers.set('Authorization', `Bearer ${token}`)
      }
    },
    onResponseError({ response, options }) {
      // Only an authenticated request failing means the session is gone (not a bad login attempt)
      if (response.status === 401 && options.headers.has('Authorization')) {
        onUnauthorized()
      }
    },
  })
}
