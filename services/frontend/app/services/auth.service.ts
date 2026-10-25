import type { AuthApi } from '~/api/endpoints/auth.api'
import type { UserResponse } from '~/types/api/responses'
import type { AuthSession, LoginCredentials, User } from '~/types/models'

export function toUser(dto: UserResponse): User {
  const initials = dto.full_name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0]!.toUpperCase())
    .join('')
  return { id: dto.id, email: dto.email, fullName: dto.full_name, initials: initials || '?' }
}

export class AuthService {
  constructor(private readonly api: AuthApi) {}

  async login({ email, password }: LoginCredentials): Promise<AuthSession> {
    const { access_token } = await this.api.login({ email: email.trim(), password })
    const user = await this.api.me(access_token)
    return { token: access_token, user: toUser(user) }
  }

  async currentUser(): Promise<User> {
    return toUser(await this.api.me())
  }
}
