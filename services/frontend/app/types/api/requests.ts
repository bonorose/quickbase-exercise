/** Request bodies / query params — mirror backend src/schemas/requests */

export interface LoginRequest {
  email: string
  password: string
}

export interface ListItemsQuery {
  limit?: number
  offset?: number
}
