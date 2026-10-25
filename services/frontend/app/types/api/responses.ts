/** Response bodies — mirror backend src/schemas/responses */

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface UserResponse {
  id: number
  email: string
  full_name: string
}

export interface ItemResponse {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface ItemListResponse {
  items: ItemResponse[]
  total: number
  limit: number
  offset: number
}

export interface HealthResponse {
  status: 'ok' | 'degraded'
  database: 'up' | 'down'
}

/** FastAPI returns a string for domain errors and a list for request validation errors */
export interface ErrorResponse {
  detail: string | { msg: string, loc: (string | number)[] }[]
}
