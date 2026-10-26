import type { AuthApi } from '~/api/endpoints/auth.api'
import type { UserResponse } from '~/types/api/responses'
import type { LoginCredentials, User } from '~/types/models'

export class MissingOrganizationError extends Error {
  constructor(message = 'Your account is not assigned to a team') {
    super(message)
    this.name = 'MissingOrganizationError'
  }
}

export function toUser(dto: UserResponse): User {
  if (!dto.organization) {
    throw new MissingOrganizationError()
  }
  const initials = dto.name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0]!.toUpperCase())
    .join('')
  return {
    id: dto.id,
    email: dto.email,
    fullName: dto.name,
    initials: initials || '?',
    role: dto.role,
    organization: { id: dto.organization.id, name: dto.organization.name },
  }
}

export class AuthService {
  constructor(private readonly api: AuthApi) {}

  async login({ email, password }: LoginCredentials): Promise<User> {
    await this.api.login({ email: email.trim(), password })
    return toUser(await this.api.me())
  }

  async currentUser(): Promise<User> {
    return toUser(await this.api.me())
  }

  async logout(): Promise<void> {
    await this.api.logout()
  }
}
