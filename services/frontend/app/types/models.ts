/** View models — what components consume. Built from API DTOs by the services layer. */

export interface User {
  id: number
  email: string
  fullName: string
  initials: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface AuthSession {
  token: string
  user: User
}

export interface ItemSummary {
  id: number
  name: string
  description: string
  createdAt: Date
}

export type ServiceStatus = 'up' | 'degraded' | 'down'

export interface DashboardSummary {
  totalItems: number
  apiStatus: ServiceStatus
  databaseStatus: ServiceStatus
  items: ItemSummary[]
}
