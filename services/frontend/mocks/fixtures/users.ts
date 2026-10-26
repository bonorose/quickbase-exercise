import type { UserResponse } from '~/types/api/responses'
import { organizations } from './organizations'

export interface FixtureUser extends UserResponse {
  password: string
}

const PASSWORD = 'admin123'

export const users: FixtureUser[] = [
  { id: 11, name: 'Excellence Lead', email: 'lead@excellence.qai.local', role: 'team_lead', organization: organizations.excellence, password: PASSWORD },
  { id: 12, name: 'Excellence Operator One', email: 'op1@excellence.qai.local', role: 'operator', organization: organizations.excellence, password: PASSWORD },
  { id: 13, name: 'Excellence Operator Two', email: 'op2@excellence.qai.local', role: 'operator', organization: organizations.excellence, password: PASSWORD },
  { id: 21, name: 'Quantum Lead', email: 'lead@quantum.qai.local', role: 'team_lead', organization: organizations.quantum, password: PASSWORD },
  { id: 22, name: 'Quantum Operator One', email: 'op1@quantum.qai.local', role: 'operator', organization: organizations.quantum, password: PASSWORD },
  { id: 23, name: 'Quantum Operator Two', email: 'op2@quantum.qai.local', role: 'operator', organization: organizations.quantum, password: PASSWORD },
]

export function findUserByEmail(email: string): FixtureUser | undefined {
  return users.find(user => user.email.toLowerCase() === email.trim().toLowerCase())
}

export function findUserById(id: number): FixtureUser | undefined {
  return users.find(user => user.id === id)
}

export function toUserResponse(user: FixtureUser): UserResponse {
  const { password: _password, ...dto } = user
  return dto
}
